import cv2
import os
import time
import threading
from datetime import datetime, timezone
from backend.extensions import db, socketio
from backend.models.metric import Metric
from backend.models.recording import Recording
from backend.services import pose_engine
from backend.services import dense_counter
from backend.services.heatmap_service import (
    SampleRateGate,
    persist_sample,
    DEFAULT_SAMPLE_INTERVAL_S,
)
from backend.utils.helpers import generate_id
from backend.utils.logger import get_logger
from config import Config

logger = get_logger('video_processor')


class VideoProcessor:
    """Processes video frames in a background thread, provides MJPEG stream."""

    def __init__(self, camera_id, source_path, ai_engine, crowd_analyzer,
                 risk_calculator, alert_manager, app,
                 area_sqm=100.0, expected_capacity=500,
                 dense_mode='auto'):
        self.camera_id = camera_id
        self.source_path = source_path
        self.ai_engine = ai_engine
        self.crowd_analyzer = crowd_analyzer
        self.risk_calculator = risk_calculator
        self.alert_manager = alert_manager
        self.app = app
        self.area_sqm = area_sqm
        self.expected_capacity = expected_capacity
        self.dense_mode = dense_mode
        self.show_heatmap = False

        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        self._latest_frame = None
        self._latest_metrics = {}
        self._frame_count = 0
        self._metric_interval = 10
        self._density_history = []
        self._risk_history = []
        self._video_writer = None
        self._recording_path = None
        self._recording_start = None
        self._recorded_frames = 0
        self._last_recording_id = None
        self._heatmap_gate = SampleRateGate(
            interval_s=getattr(Config, 'HEATMAP_SAMPLE_INTERVAL_S',
                               DEFAULT_SAMPLE_INTERVAL_S)
        )
        self._pose_interval = 5  # analyze pose every Nth processed frame
        self._last_pose_feats = None
        self._dense_interval = max(1, getattr(Config, 'DENSE_COUNT_INTERVAL', 15))
        self._last_dense_count = None  # latest DenseCount result

    @property
    def is_running(self):
        return self._running

    @property
    def latest_metrics(self):
        return self._latest_metrics.copy()

    @property
    def last_recording_id(self):
        return self._last_recording_id

    def start(self):
        if self._running:
            return
        self._running = True
        self.ai_engine.reset_tracker()
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=15)
            self._thread = None

    def get_frame(self):
        with self._lock:
            return self._latest_frame

    def generate_mjpeg(self):
        while self._running:
            frame = self.get_frame()
            if frame is not None:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(1.0 / 15)

    def _process_loop(self):
        cap = cv2.VideoCapture(self.source_path)
        if not cap.isOpened():
            logger.error(f"Cannot open video: {self.source_path}")
            self._running = False
            self._update_camera_status('error')
            return

        self._update_camera_status('processing')
        socketio.emit('camera_status', {'camera_id': self.camera_id, 'status': 'processing'})

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_delay = 1.0 / min(fps, 30)

        try:
            while self._running:
                ret, frame = cap.read()
                if not ret:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    self.ai_engine.reset_tracker()
                    self._frame_count = 0
                    continue

                self._frame_count += 1

                # Resize large frames
                h, w = frame.shape[:2]
                if w > 1280:
                    scale = 1280 / w
                    frame = cv2.resize(frame, (1280, int(h * scale)))

                # AI detection + tracking
                raw_frame, analysis = self.ai_engine.analyze_frame(
                    frame, self.area_sqm, self.expected_capacity, int(fps)
                )

                detections = analysis.get('detections', [])

                # CSRNet dense counting — overrides YOLO count when the scene
                # exceeds the bbox detector's reliable range. Tracking and
                # clustering still run off YOLO; only count/density change.
                if (Config.DENSE_COUNT_ENABLED
                        and self._frame_count % self._dense_interval == 0
                        and dense_counter.should_use_dense(
                            analysis.get('count', 0), self.dense_mode)):
                    try:
                        dc = dense_counter.analyze_frame(frame)
                        if dc is not None and dc.backend == 'csrnet':
                            self._last_dense_count = dc
                            try:
                                from backend.observability import record_dense_invocation
                                record_dense_invocation()
                            except Exception:
                                pass
                    except Exception as e:
                        logger.debug(f"Dense count skipped: {e}")

                if self._last_dense_count is not None:
                    dense_n = self._last_dense_count.count
                    if dense_n > analysis.get('count', 0):
                        analysis['count'] = dense_n
                        analysis['density'] = (
                            dense_n / self.area_sqm if self.area_sqm > 0 else 0
                        )
                        analysis['method'] = 'csrnet_density'
                        if self.expected_capacity > 0:
                            analysis['capacity_utilization'] = (
                                dense_n / self.expected_capacity * 100
                            )

                # ML crowd analysis (clustering, anomalies, flow, pressure)
                ml_analysis = self.crowd_analyzer.analyze(
                    detections,
                    self.ai_engine.track_history,
                    frame.shape,
                )

                # Pose-fusion crush detection (every Nth frame; best-effort)
                if (Config.POSE_ENABLED
                        and self._frame_count % self._pose_interval == 0):
                    try:
                        pose_feats = pose_engine.analyze_frame(
                            frame, density=analysis.get('density', 0.0),
                        )
                        if pose_feats is not None:
                            self._last_pose_feats = pose_feats
                    except Exception as e:
                        logger.debug(f"Pose analysis skipped: {e}")

                if self._last_pose_feats is not None:
                    pf = self._last_pose_feats
                    ml_analysis['pose'] = {
                        'n_persons': pf.n_persons,
                        'n_fallen': pf.n_fallen,
                        'n_compressed': pf.n_compressed,
                        'n_arms_up': pf.n_arms_up,
                        'crush_risk': round(pf.crush_risk, 3),
                    }

                # Risk scoring (enhanced with ML signals)
                risk_score, risk_level = self.risk_calculator.calculate(
                    density=analysis['density'],
                    avg_velocity=analysis['avg_velocity'],
                    surge_rate=analysis['surge_rate'],
                    count=analysis['count'],
                    crowd_pressure=ml_analysis.get('crowd_pressure', 0),
                    flow_coherence=ml_analysis.get('flow_coherence', 0),
                )

                # Crush amplifier: pose-derived crush_risk escalates risk.
                # Any fallen or heavily compressed person is CRITICAL regardless of density.
                pose_block = ml_analysis.get('pose') or {}
                crush_risk = pose_block.get('crush_risk', 0.0) or 0.0
                crush_amp = getattr(Config, 'RISK_CRUSH_AMPLIFIER', 0.4)
                crush_critical = getattr(Config, 'RISK_CRUSH_CRITICAL_THRESHOLD', 0.6)
                crush_warning = getattr(Config, 'RISK_CRUSH_WARNING_THRESHOLD', 0.3)
                if crush_risk > 0:
                    risk_score = max(risk_score, min(1.0, risk_score + crush_amp * crush_risk))
                if pose_block.get('n_fallen', 0) > 0 or crush_risk >= crush_critical:
                    risk_level = 'CRITICAL'
                elif crush_risk >= crush_warning and risk_level == 'SAFE':
                    risk_level = 'WARNING'

                # Feed trend prediction
                self.crowd_analyzer.update_history(
                    analysis['density'], analysis['count'], risk_score
                )

                # Track density/risk history for sparkline chart
                self._density_history.append(analysis['density'])
                self._risk_history.append(risk_score)
                if len(self._density_history) > 120:
                    self._density_history = self._density_history[-120:]
                    self._risk_history = self._risk_history[-120:]
                ml_analysis['density_history'] = self._density_history
                ml_analysis['risk_history'] = self._risk_history

                # Professional multi-layer annotation
                annotated = self.ai_engine.annotate_frame(
                    raw_frame, detections, ml_analysis, risk_level, risk_score
                )

                # Optional heatmap overlay
                if self.show_heatmap and analysis.get('density_map') is not None:
                    annotated = self.ai_engine.create_heatmap_overlay(
                        annotated, analysis['density_map']
                    )

                # Write annotated frame to recording file
                self._write_recording_frame(annotated, fps)

                # Encode JPEG
                _, jpeg = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
                with self._lock:
                    self._latest_frame = jpeg.tobytes()

                metrics = {
                    'camera_id': self.camera_id,
                    'count': analysis['count'],
                    'density': round(analysis['density'], 3),
                    'avg_velocity': round(analysis['avg_velocity'], 2),
                    'max_velocity': round(analysis['max_velocity'], 2),
                    'surge_rate': round(analysis['surge_rate'], 3),
                    'flow_in': analysis.get('flow_in', 0),
                    'flow_out': analysis.get('flow_out', 0),
                    'risk_score': round(risk_score, 3),
                    'risk_level': risk_level,
                    'capacity_utilization': round(analysis.get('capacity_utilization', 0), 1),
                    'num_clusters': ml_analysis.get('num_clusters', 0),
                    'flow_coherence': ml_analysis.get('flow_coherence', 0),
                    'crowd_pressure': ml_analysis.get('crowd_pressure', 0),
                    'num_anomalies': len(ml_analysis.get('anomalies', [])),
                    'density_trend': ml_analysis.get('trend_prediction', {}).get('density_trend', 'stable'),
                    'risk_trend': ml_analysis.get('trend_prediction', {}).get('risk_trend', 'stable'),
                    'pose': ml_analysis.get('pose'),
                    'dense_count': (
                        self._last_dense_count.count
                        if self._last_dense_count is not None else None
                    ),
                    'count_method': analysis.get('method', 'direct_detection'),
                    'frame_number': self._frame_count,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                }
                self._latest_metrics = metrics

                try:
                    from backend.observability import set_risk_score
                    set_risk_score(self.camera_id, risk_score)
                except Exception:
                    pass

                socketio.emit('metrics_update', metrics, room=f'camera_{self.camera_id}')

                if self._frame_count % self._metric_interval == 0:
                    self._save_metric(metrics)

                if self._heatmap_gate.should_sample():
                    self._save_heatmap_sample(
                        analysis.get('density_map'), analysis['count']
                    )

                self.alert_manager.check_and_alert(self.camera_id, metrics, self.app, frame_jpeg=self._latest_frame)

                time.sleep(frame_delay)

        except Exception as e:
            logger.error(f"Error processing camera {self.camera_id}: {e}")
        finally:
            cap.release()
            self._finalize_recording()
            self._running = False
            self._update_camera_status('offline')
            socketio.emit('camera_status', {
                'camera_id': self.camera_id,
                'status': 'offline',
                'recording_id': self._last_recording_id,
            })

    def _write_recording_frame(self, frame, fps):
        """Initialize video writer on first frame, then write each annotated frame."""
        if self._video_writer is None:
            rec_dir = self.app.config.get('RECORDING_FOLDER', 'recordings')
            os.makedirs(rec_dir, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{self.camera_id}_{ts}_analyzed.mp4"
            self._recording_path = os.path.join(rec_dir, filename)
            self._recording_start = datetime.now(timezone.utc)
            h, w = frame.shape[:2]
            out_fps = min(fps, 30) or 15
            # Try H.264, fall back to mp4v
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            self._video_writer = cv2.VideoWriter(
                self._recording_path, fourcc, out_fps, (w, h)
            )
            if not self._video_writer.isOpened():
                logger.warning("VideoWriter failed to open, recording disabled")
                self._video_writer = None
                return
            self._recorded_frames = 0
        self._video_writer.write(frame)
        self._recorded_frames += 1

    def _finalize_recording(self):
        """Release the video writer and create a Recording DB entry."""
        if self._video_writer is None:
            return
        try:
            self._video_writer.release()
            self._video_writer = None
            if not self._recording_path or not os.path.exists(self._recording_path):
                return
            file_size = os.path.getsize(self._recording_path)
            if file_size < 1000:
                # Too small, probably empty
                os.remove(self._recording_path)
                return
            cap = cv2.VideoCapture(self._recording_path)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            rec_fps = cap.get(cv2.CAP_PROP_FPS) or 15
            cap.release()
            duration = self._recorded_frames / max(rec_fps, 1)
            rec_id = generate_id('REC')
            with self.app.app_context():
                rec = Recording(
                    recording_id=rec_id,
                    camera_id=self.camera_id,
                    filename=os.path.basename(self._recording_path),
                    filepath=self._recording_path,
                    start_time=self._recording_start,
                    end_time=datetime.now(timezone.utc),
                    duration_seconds=duration,
                    frame_count=self._recorded_frames,
                    width=width,
                    height=height,
                    fps=rec_fps,
                    file_size_bytes=file_size,
                    trigger_type='analysis',
                )
                db.session.add(rec)
                db.session.commit()
            self._last_recording_id = rec_id
            logger.info(f"Recording saved: {rec_id} ({self._recorded_frames} frames)")
        except Exception as e:
            logger.error(f"Error finalizing recording: {e}")

    def _save_heatmap_sample(self, density_map, count):
        """Throttled heatmap persistence — runs at most every N seconds."""
        if density_map is None:
            return
        try:
            with self.app.app_context():
                persist_sample(self.camera_id, density_map, int(count or 0))
        except Exception as e:
            logger.debug(f"Heatmap persist skipped: {e}")

    def _save_metric(self, metrics):
        try:
            with self.app.app_context():
                m = Metric(
                    camera_id=metrics['camera_id'],
                    count=metrics['count'],
                    density=metrics['density'],
                    avg_velocity=metrics['avg_velocity'],
                    max_velocity=metrics['max_velocity'],
                    surge_rate=metrics['surge_rate'],
                    flow_in=metrics.get('flow_in', 0),
                    flow_out=metrics.get('flow_out', 0),
                    risk_score=metrics['risk_score'],
                    risk_level=metrics['risk_level'],
                    capacity_utilization=metrics.get('capacity_utilization', 0),
                    frame_number=metrics['frame_number'],
                )
                db.session.add(m)
                db.session.commit()
        except Exception as e:
            logger.error(f"DB save error: {e}")

    def _update_camera_status(self, status):
        try:
            with self.app.app_context():
                from backend.models.camera import Camera
                cam = db.session.get(Camera, self.camera_id)
                if cam:
                    cam.status = status
                    db.session.commit()
        except Exception as e:
            logger.error(f"Status update error: {e}")

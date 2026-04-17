"""
CrowdSafe AI Engine - YOLOv11 + BoT-SORT + Professional Visualization.

Detection: YOLOv11s (small) for better accuracy than nano.
Tracking: BoT-SORT with Kalman filter + appearance matching.
Visualization: Corner-style bounding boxes, proximity halos,
  cluster outlines, flow direction arrows, confidence bars.
"""

import cv2
import numpy as np
import os
import time
import threading
from ultralytics import YOLO
from backend.utils.logger import get_logger

logger = get_logger('ai_engine')

# Color palette - BGR format
COLOR_SAFE = (100, 200, 60)       # bright green
COLOR_CAUTION = (0, 210, 255)     # gold/amber
COLOR_WARNING = (0, 120, 255)     # deep orange
COLOR_CRITICAL = (50, 50, 230)    # red
COLOR_CLUSTER = (255, 180, 50)    # light blue
COLOR_ANOMALY = (80, 0, 200)      # purple (distinct from critical red)
COLOR_PROXIMITY = (50, 160, 255)  # bright orange
COLOR_FLOW = (200, 200, 50)       # teal (distinct from cluster)
COLOR_HUD_BG = (15, 15, 15)      # darker for contrast
COLOR_HUD_TEXT = (245, 245, 245)  # brighter for readability
COLOR_HUD_ACCENT = (255, 200, 50)


class CrowdSafeAI:
    """YOLOv11s + BoT-SORT person detection, tracking, and annotation."""

    def __init__(self, config):
        self.config = config
        self._lock = threading.Lock()

        model_path = os.path.join(config.MODEL_FOLDER, config.YOLO_MODEL)
        logger.info(f"Loading YOLO model: {config.YOLO_MODEL}")
        self.model = YOLO(model_path)

        self.track_history = {}
        self.dense_crowd_threshold = getattr(config, 'DENSE_CROWD_THRESHOLD', 50)
        self.grid_size = getattr(config, 'GRID_SIZE', 50)
        self.occlusion_factor = getattr(config, 'OCCLUSION_FACTOR', 1.3)
        self.pixel_to_meter = 1.0 / getattr(config, 'PIXELS_PER_METER', 100.0)
        self.imgsz = getattr(config, 'YOLO_IMGSZ', 960)
        self.min_box_area = getattr(config, 'YOLO_MIN_BOX_AREA', 400)
        self.max_box_ratio = getattr(config, 'YOLO_MAX_BOX_RATIO', 5.0)

    def reset_tracker(self):
        with self._lock:
            if hasattr(self.model, 'predictor') and self.model.predictor is not None:
                self.model.predictor = None
            self.track_history.clear()

    def analyze_frame(self, frame, area_sqm=100.0, expected_capacity=500, fps=30):
        start_time = time.time()

        # Copy BEFORE YOLO - tracker may modify source frame in-place
        clean_frame = frame.copy()

        with self._lock:
            results = self.model.track(
                frame,
                persist=True,
                tracker='botsort.yaml',
                classes=[0],
                conf=self.config.YOLO_CONFIDENCE,
                iou=self.config.YOLO_IOU,
                imgsz=self.imgsz,
                verbose=False,
            )

        annotated = clean_frame
        detections = []
        velocities = []
        current_time = time.time()

        if results and len(results) > 0:
            result = results[0]
            boxes_obj = result.boxes

            if boxes_obj is not None and len(boxes_obj) > 0:
                xyxy = boxes_obj.xyxy.cpu().numpy()
                confs = boxes_obj.conf.cpu().numpy()
                track_ids = boxes_obj.id
                if track_ids is not None:
                    track_ids = track_ids.cpu().numpy().astype(int)
                else:
                    track_ids = np.arange(len(xyxy))

                for box, conf, tid in zip(xyxy, confs, track_ids):
                    x1, y1, x2, y2 = box.astype(int)
                    bw, bh = x2 - x1, y2 - y1
                    # Filter out false positives: too small or too thin
                    if bw * bh < self.min_box_area:
                        continue
                    aspect = max(bw, bh) / max(min(bw, bh), 1)
                    if aspect > self.max_box_ratio:
                        continue
                    cx = (x1 + x2) / 2.0
                    cy = (y1 + y2) / 2.0

                    if tid not in self.track_history:
                        self.track_history[tid] = []
                    self.track_history[tid].append((cx, cy, current_time))
                    if len(self.track_history[tid]) > 60:
                        self.track_history[tid] = self.track_history[tid][-60:]

                    # Velocity from track displacement
                    velocity = 0.0
                    direction = (0.0, 0.0)
                    hist = self.track_history[tid]
                    if len(hist) >= 2:
                        prev_cx, prev_cy, prev_t = hist[-2]
                        dx = cx - prev_cx
                        dy = cy - prev_cy
                        dist_px = np.sqrt(dx * dx + dy * dy)
                        dt = current_time - prev_t
                        if dt > 0:
                            velocity = (dist_px * self.pixel_to_meter) / dt
                        mag = max(dist_px, 1e-6)
                        direction = (dx / mag, dy / mag)
                    velocities.append(velocity)

                    detections.append({
                        'track_id': int(tid),
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': float(conf),
                        'center': (cx, cy),
                        'velocity': velocity,
                        'direction': direction,
                    })

        # Clean stale tracks
        active_ids = {d['track_id'] for d in detections}
        stale_cutoff = current_time - 3.0
        for tid in list(self.track_history.keys()):
            if tid not in active_ids:
                if self.track_history[tid][-1][2] < stale_cutoff:
                    del self.track_history[tid]

        # Count and density
        raw_count = len(detections)
        if raw_count >= self.dense_crowd_threshold:
            estimated_count = self._estimate_dense_crowd(frame, [d['bbox'] for d in detections])
            method = 'grid_estimation'
        else:
            estimated_count = raw_count
            method = 'direct_detection'

        density = estimated_count / area_sqm if area_sqm > 0 else 0
        avg_velocity = float(np.mean(velocities)) if velocities else 0.0
        max_velocity = float(np.max(velocities)) if velocities else 0.0
        capacity_util = (estimated_count / expected_capacity * 100) if expected_capacity > 0 else 0

        # Surge detection
        surge_rate = 0.0
        if len(velocities) > 2:
            vel_std = float(np.std(velocities))
            vel_mean = float(np.mean(velocities))
            if vel_mean > 0.3:
                surge_rate = min(1.0, vel_std / (vel_mean + 1e-6))

        # Density heatmap
        density_map = self._create_density_map(frame, [d['bbox'] for d in detections])

        processing_time = (time.time() - start_time) * 1000

        return annotated, {
            'count': estimated_count,
            'density': density,
            'avg_velocity': avg_velocity,
            'max_velocity': max_velocity,
            'surge_rate': surge_rate,
            'flow_in': 0,
            'flow_out': 0,
            'capacity_utilization': capacity_util,
            'detections': detections,
            'density_map': density_map,
            'method': method,
            'processing_time_ms': round(processing_time, 2),
        }

    def annotate_frame(self, frame, detections, ml_analysis, risk_level, risk_score):
        """
        Professional annotation pass. Called separately so video_processor
        can pass ML results from crowd_analyzer.
        """
        annotated = frame.copy()

        # Layer 1: Cluster outlines
        self._draw_clusters(annotated, detections, ml_analysis)

        # Layer 2: Proximity warning lines
        self._draw_proximity(annotated, ml_analysis)

        # Layer 3: Flow direction arrows
        self._draw_flow_arrows(annotated, ml_analysis)

        # Layer 4: Per-person bounding boxes (corner style)
        self._draw_detections(annotated, detections, ml_analysis)

        # Layer 5: HUD panel
        self._draw_hud(annotated, detections, ml_analysis, risk_level, risk_score)

        # Layer 6: Sparkline chart (density + risk history)
        self._draw_sparkline_chart(annotated, ml_analysis)

        return annotated

    # ---- Drawing: Corner-style bounding boxes ----

    def _draw_detections(self, frame, detections, ml_analysis):
        anomaly_ids = {a['track_id'] for a in ml_analysis.get('anomalies', [])}

        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            tid = det['track_id']
            conf = det['confidence']
            vel = det['velocity']

            # Color by proximity/anomaly status
            if tid in anomaly_ids:
                color = COLOR_ANOMALY
            elif vel > 1.5:
                color = COLOR_WARNING
            elif vel > 0.8:
                color = COLOR_CAUTION
            else:
                color = COLOR_SAFE

            # Corner-style bounding box
            self._draw_corner_box(frame, x1, y1, x2, y2, color, thickness=2)

            # Label: ID + confidence
            label = f"#{tid}  {conf:.0%}"
            self._draw_label(frame, label, x1, y1 - 4, color)

            # Direction indicator (small arrow from center)
            dx, dy = det.get('direction', (0, 0))
            if abs(dx) + abs(dy) > 0.1:
                cx, cy = int((x1 + x2) / 2), int(y2 - 5)
                ex, ey = int(cx + dx * 20), int(cy + dy * 20)
                cv2.arrowedLine(frame, (cx, cy), (ex, ey), color, 1, tipLength=0.4)

            # Velocity trail (fading)
            hist = self.track_history.get(tid, [])
            if len(hist) > 2:
                pts = [(int(p[0]), int(p[1])) for p in hist[-15:]]
                for k in range(1, len(pts)):
                    alpha = k / len(pts)
                    c = tuple(int(ch * alpha) for ch in color)
                    cv2.line(frame, pts[k - 1], pts[k], c, 1, cv2.LINE_AA)

    @staticmethod
    def _draw_corner_box(frame, x1, y1, x2, y2, color, thickness=2, corner_len=12):
        """Draw corners-only bounding box (professional CCTV style)."""
        cl = corner_len

        # Top-left
        cv2.line(frame, (x1, y1), (x1 + cl, y1), color, thickness, cv2.LINE_AA)
        cv2.line(frame, (x1, y1), (x1, y1 + cl), color, thickness, cv2.LINE_AA)
        # Top-right
        cv2.line(frame, (x2, y1), (x2 - cl, y1), color, thickness, cv2.LINE_AA)
        cv2.line(frame, (x2, y1), (x2, y1 + cl), color, thickness, cv2.LINE_AA)
        # Bottom-left
        cv2.line(frame, (x1, y2), (x1 + cl, y2), color, thickness, cv2.LINE_AA)
        cv2.line(frame, (x1, y2), (x1, y2 - cl), color, thickness, cv2.LINE_AA)
        # Bottom-right
        cv2.line(frame, (x2, y2), (x2 - cl, y2), color, thickness, cv2.LINE_AA)
        cv2.line(frame, (x2, y2), (x2, y2 - cl), color, thickness, cv2.LINE_AA)

        # Thin connecting lines (subtle)
        thin = max(1, thickness - 1)
        faint = tuple(int(c * 0.3) for c in color)
        cv2.rectangle(frame, (x1, y1), (x2, y2), faint, thin, cv2.LINE_AA)

    @staticmethod
    def _draw_label(frame, text, x, y, color):
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.4
        thick = 1
        (tw, th), baseline = cv2.getTextSize(text, font, scale, thick)
        y_top = max(y - th - 4, 0)
        overlay = frame.copy()
        cv2.rectangle(overlay, (x, y_top), (x + tw + 6, y_top + th + 4), COLOR_HUD_BG, -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        cv2.putText(frame, text, (x + 3, y_top + th + 1), font, scale, color, thick, cv2.LINE_AA)

    # ---- Drawing: Clusters ----

    def _draw_clusters(self, frame, detections, ml_analysis):
        clusters = ml_analysis.get('clusters', {})
        labels = clusters.get('labels', [])
        centers = clusters.get('cluster_centers', [])
        sizes = clusters.get('cluster_sizes', [])

        if not labels or not centers:
            return

        # Draw convex hull around each cluster
        for k, (ccx, ccy) in enumerate(centers):
            cluster_points = []
            for i, lbl in enumerate(labels):
                if lbl == k and i < len(detections):
                    cx, cy = detections[i]['center']
                    cluster_points.append([int(cx), int(cy)])

            if len(cluster_points) >= 3:
                pts = np.array(cluster_points)
                hull = cv2.convexHull(pts)
                # Expand hull slightly
                M = cv2.moments(hull)
                if M['m00'] > 0:
                    hcx = int(M['m10'] / M['m00'])
                    hcy = int(M['m01'] / M['m00'])
                    expanded = []
                    for p in hull:
                        px, py = p[0]
                        dx = px - hcx
                        dy = py - hcy
                        expanded.append([[int(px + dx * 0.15), int(py + dy * 0.15)]])
                    expanded = np.array(expanded)
                    overlay = frame.copy()
                    cv2.polylines(overlay, [expanded], True, COLOR_CLUSTER, 2, cv2.LINE_AA)
                    cv2.fillConvexPoly(overlay, expanded, (*COLOR_CLUSTER[:2], 20))
                    cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)

            # Cluster label
            cv2.putText(frame, f"G{k+1}:{sizes[k]}", (int(ccx) - 15, int(ccy) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, COLOR_CLUSTER, 1, cv2.LINE_AA)

    # ---- Drawing: Proximity warnings ----

    def _draw_proximity(self, frame, ml_analysis):
        for alert in ml_analysis.get('proximity_alerts', [])[:20]:
            mx, my = int(alert['midpoint'][0]), int(alert['midpoint'][1])
            dist = alert['distance_px']
            intensity = max(0.3, 1.0 - dist / 100.0)
            color = (0, int(80 * intensity), int(255 * intensity))
            cv2.circle(frame, (mx, my), int(dist / 2), color, 1, cv2.LINE_AA)

    # ---- Drawing: Flow arrows ----

    def _draw_flow_arrows(self, frame, ml_analysis):
        for fv in ml_analysis.get('flow_vectors', []):
            cx, cy = int(fv['cx']), int(fv['cy'])
            dx, dy = fv['dx'], fv['dy']
            mag = fv['magnitude']
            length = min(30, max(10, mag * 0.5))
            ex = int(cx + dx * length)
            ey = int(cy + dy * length)
            cv2.arrowedLine(frame, (cx, cy), (ex, ey), COLOR_FLOW, 1, cv2.LINE_AA, tipLength=0.3)

    # ---- Drawing: HUD ----

    def _draw_hud(self, frame, detections, ml_analysis, risk_level, risk_score):
        h, w = frame.shape[:2]

        # Top-left: stats panel
        panel_w, panel_h = 260, 130
        overlay = frame.copy()
        cv2.rectangle(overlay, (8, 8), (8 + panel_w, 8 + panel_h), COLOR_HUD_BG, -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        font = cv2.FONT_HERSHEY_SIMPLEX
        y_off = 28
        lines = [
            (f"People: {len(detections)}", COLOR_HUD_TEXT),
            (f"Clusters: {ml_analysis.get('num_clusters', 0)}", COLOR_HUD_TEXT),
            (f"Coherence: {ml_analysis.get('flow_coherence', 0):.2f}", COLOR_HUD_TEXT),
            (f"Pressure: {ml_analysis.get('crowd_pressure', 0):.2f}", COLOR_HUD_TEXT),
        ]
        for text, color in lines:
            cv2.putText(frame, text, (18, y_off), font, 0.5, color, 1, cv2.LINE_AA)
            y_off += 22

        trend = ml_analysis.get('trend_prediction', {})
        trend_text = f"Trend: {trend.get('risk_trend', 'stable')}"
        trend_color = COLOR_CRITICAL if trend.get('risk_trend') == 'increasing' else COLOR_SAFE
        cv2.putText(frame, trend_text, (18, y_off), font, 0.5, trend_color, 1, cv2.LINE_AA)

        # Top-right: risk badge
        risk_colors = {
            'SAFE': COLOR_SAFE, 'CAUTION': COLOR_CAUTION,
            'WARNING': COLOR_WARNING, 'CRITICAL': COLOR_CRITICAL,
        }
        rcolor = risk_colors.get(risk_level, COLOR_HUD_TEXT)
        label = f"{risk_level} {risk_score:.0%}"
        (tw, th), _ = cv2.getTextSize(label, font, 0.7, 2)
        rx = w - tw - 20

        overlay2 = frame.copy()
        cv2.rectangle(overlay2, (rx - 12, 8), (w - 5, 45), COLOR_HUD_BG, -1)
        cv2.addWeighted(overlay2, 0.75, frame, 0.25, 0, frame)
        cv2.putText(frame, label, (rx, 36), font, 0.7, rcolor, 2, cv2.LINE_AA)

        # Anomaly count badge
        n_anomalies = len(ml_analysis.get('anomalies', []))
        if n_anomalies > 0:
            badge = f"{n_anomalies} anomal{'ies' if n_anomalies > 1 else 'y'}"
            cv2.putText(frame, badge, (rx, 60), font, 0.4, COLOR_ANOMALY, 1, cv2.LINE_AA)

    # ---- Drawing: Sparkline chart ----

    def _draw_sparkline_chart(self, frame, ml_analysis):
        """Draw a small semi-transparent sparkline chart in the top-right showing
        density and risk history over time."""
        density_hist = ml_analysis.get('density_history', [])
        risk_hist = ml_analysis.get('risk_history', [])
        if len(density_hist) < 3 and len(risk_hist) < 3:
            return

        h, w = frame.shape[:2]
        chart_w, chart_h = 180, 70
        margin = 10
        x0 = w - chart_w - margin
        y0 = 55  # below risk badge
        x1 = x0 + chart_w
        y1 = y0 + chart_h

        # Semi-transparent background
        overlay = frame.copy()
        cv2.rectangle(overlay, (x0, y0), (x1, y1), COLOR_HUD_BG, -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        cv2.rectangle(frame, (x0, y0), (x1, y1), (40, 40, 40), 1, cv2.LINE_AA)

        def draw_line(data, max_val, color):
            if len(data) < 2:
                return
            n = min(len(data), 60)
            pts = []
            for i, v in enumerate(data[-60:]):  # last 60 points
                px = x0 + 4 + int(i * (chart_w - 8) / max(n - 1, 1))
                clamped = min(v / max(max_val, 1e-6), 1.0)
                py = y1 - 4 - int(clamped * (chart_h - 8))
                pts.append((px, py))
            for k in range(1, len(pts)):
                cv2.line(frame, pts[k - 1], pts[k], color, 1, cv2.LINE_AA)

        # Green line = density (max 10 p/m²)
        draw_line(density_hist, 10.0, COLOR_SAFE)
        # Red line = risk (max 1.0)
        draw_line(risk_hist, 1.0, COLOR_CRITICAL)

        # Legend dots
        font = cv2.FONT_HERSHEY_SIMPLEX
        ly = y1 + 12
        cv2.circle(frame, (x0 + 4, ly), 3, COLOR_SAFE, -1, cv2.LINE_AA)
        cv2.putText(frame, "density", (x0 + 10, ly + 3), font, 0.28, COLOR_HUD_TEXT, 1, cv2.LINE_AA)
        cv2.circle(frame, (x0 + 65, ly), 3, COLOR_CRITICAL, -1, cv2.LINE_AA)
        cv2.putText(frame, "risk", (x0 + 71, ly + 3), font, 0.28, COLOR_HUD_TEXT, 1, cv2.LINE_AA)

    # ---- Heatmap ----

    def create_heatmap_overlay(self, frame, density_map, alpha=0.4):
        if density_map is None or density_map.max() == 0:
            return frame
        h, w = frame.shape[:2]
        dm = cv2.resize(density_map, (w, h))
        hm_norm = (dm * 255).astype(np.uint8)
        hm_colored = cv2.applyColorMap(hm_norm, cv2.COLORMAP_JET)
        return cv2.addWeighted(frame, 1 - alpha, hm_colored, alpha, 0)

    # ---- Dense crowd estimation ----

    def _estimate_dense_crowd(self, frame, boxes):
        h, w = frame.shape[:2]
        gh = max(1, h // self.grid_size)
        gw = max(1, w // self.grid_size)
        grid = np.zeros((gh, gw))

        for box in boxes:
            x1, y1, x2, y2 = box
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            gx = min(int(cx / self.grid_size), gw - 1)
            gy = min(int(cy / self.grid_size), gh - 1)
            if 0 <= gx < gw and 0 <= gy < gh:
                grid[gy, gx] += 1

        occupied = grid > 0
        if occupied.sum() > 0:
            avg_per_grid = grid[occupied].mean()
            return int(occupied.sum() * avg_per_grid * self.occlusion_factor)
        return len(boxes)

    def _create_density_map(self, frame, boxes):
        h, w = frame.shape[:2]
        density_map = np.zeros((h // 4, w // 4), dtype=np.float32)
        sigma = 15

        for box in boxes:
            x1, y1, x2, y2 = box
            cx, cy = int((x1 + x2) // 2 // 4), int((y1 + y2) // 2 // 4)
            ks = 30
            dh, dw = density_map.shape
            y_lo, y_hi = max(0, cy - ks), min(dh, cy + ks)
            x_lo, x_hi = max(0, cx - ks), min(dw, cx + ks)
            if y_lo >= y_hi or x_lo >= x_hi:
                continue
            yy, xx = np.ogrid[y_lo:y_hi, x_lo:x_hi]
            g = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma ** 2))
            density_map[y_lo:y_hi, x_lo:x_hi] += g

        if density_map.max() > 0:
            density_map /= density_map.max()
        return density_map

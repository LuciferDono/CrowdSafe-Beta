"""
Crowd Behavior Analyzer - ML-based analysis layer.

Runs on top of raw YOLO detections to produce higher-level intelligence:
  - DBSCAN spatial clustering (group detection)
  - Per-person proximity scoring (social distance)
  - Anomaly detection via velocity z-score
  - Crowd flow coherence (stampede indicator)
  - Movement direction field
  - Temporal trend prediction using exponential moving average
"""

import numpy as np
from collections import deque
from sklearn.cluster import DBSCAN


class CrowdAnalyzer:

    def __init__(self, config):
        self.proximity_thresh = getattr(config, 'PROXIMITY_THRESHOLD_PX', 80)
        self.cluster_eps = getattr(config, 'CLUSTER_EPS_PX', 120)
        self.cluster_min = getattr(config, 'CLUSTER_MIN_SAMPLES', 2)
        self.anomaly_zscore = getattr(config, 'ANOMALY_VELOCITY_ZSCORE', 2.0)
        self.coherence_window = getattr(config, 'COHERENCE_WINDOW', 10)

        # Rolling history for trend prediction
        self._density_history = deque(maxlen=60)
        self._count_history = deque(maxlen=60)
        self._risk_history = deque(maxlen=60)

        # Per-track direction vectors for coherence
        self._direction_vectors = {}

    def analyze(self, detections, track_history, frame_shape):
        """
        Takes raw detections from ai_engine and produces ML analysis.

        Args:
            detections: list of dicts with track_id, bbox, center, velocity, confidence
            track_history: dict {track_id: [(cx, cy, t), ...]}
            frame_shape: (h, w, c)

        Returns dict with:
            clusters, proximity_alerts, anomalies, flow_coherence,
            flow_vectors, crowd_pressure, trend_prediction
        """
        if len(detections) == 0:
            return self._empty_result()

        centers = np.array([d['center'] for d in detections], dtype=np.float64)
        velocities = np.array([d['velocity'] for d in detections], dtype=np.float64)
        track_ids = [d['track_id'] for d in detections]

        # 1) DBSCAN clustering
        clusters = self._cluster_people(centers)

        # 2) Proximity scoring
        proximity_alerts = self._proximity_analysis(centers, track_ids)

        # 3) Velocity anomaly detection
        anomalies = self._detect_anomalies(velocities, track_ids)

        # 4) Flow coherence (stampede indicator)
        flow_coherence, flow_vectors = self._flow_analysis(
            track_ids, track_history, centers
        )

        # 5) Crowd pressure estimation
        crowd_pressure = self._crowd_pressure(centers, velocities, frame_shape)

        # 6) Trend prediction
        trend = self._trend_prediction()

        return {
            'clusters': clusters,
            'num_clusters': int(clusters['n_clusters']),
            'proximity_alerts': proximity_alerts,
            'anomalies': anomalies,
            'flow_coherence': round(flow_coherence, 3),
            'flow_vectors': flow_vectors,
            'crowd_pressure': round(crowd_pressure, 3),
            'trend_prediction': trend,
        }

    def update_history(self, density, count, risk_score):
        """Call after each frame to feed trend prediction."""
        self._density_history.append(density)
        self._count_history.append(count)
        self._risk_history.append(risk_score)

    # ---- DBSCAN Clustering ----

    def _cluster_people(self, centers):
        if len(centers) < self.cluster_min:
            return {'n_clusters': 0, 'labels': [], 'cluster_centers': [], 'cluster_sizes': []}

        db = DBSCAN(eps=self.cluster_eps, min_samples=self.cluster_min)
        labels = db.fit_predict(centers)

        unique_labels = set(labels)
        unique_labels.discard(-1)
        n_clusters = len(unique_labels)

        cluster_centers = []
        cluster_sizes = []
        for k in sorted(unique_labels):
            mask = labels == k
            cluster_points = centers[mask]
            cx = float(cluster_points[:, 0].mean())
            cy = float(cluster_points[:, 1].mean())
            cluster_centers.append((cx, cy))
            cluster_sizes.append(int(mask.sum()))

        return {
            'n_clusters': n_clusters,
            'labels': labels.tolist(),
            'cluster_centers': cluster_centers,
            'cluster_sizes': cluster_sizes,
        }

    # ---- Proximity ----

    def _proximity_analysis(self, centers, track_ids):
        alerts = []
        n = len(centers)
        if n < 2:
            return alerts

        # Pairwise distance matrix
        diffs = centers[:, np.newaxis, :] - centers[np.newaxis, :, :]
        dists = np.sqrt((diffs ** 2).sum(axis=2))

        for i in range(n):
            for j in range(i + 1, n):
                if dists[i, j] < self.proximity_thresh:
                    alerts.append({
                        'pair': (track_ids[i], track_ids[j]),
                        'distance_px': round(float(dists[i, j]), 1),
                        'midpoint': (
                            float((centers[i][0] + centers[j][0]) / 2),
                            float((centers[i][1] + centers[j][1]) / 2),
                        ),
                    })
        return alerts

    # ---- Anomaly Detection ----

    def _detect_anomalies(self, velocities, track_ids):
        anomalies = []
        if len(velocities) < 3:
            return anomalies

        mean_v = velocities.mean()
        std_v = velocities.std()
        if std_v < 0.01:
            return anomalies

        z_scores = (velocities - mean_v) / std_v

        for i, (z, v, tid) in enumerate(zip(z_scores, velocities, track_ids)):
            if abs(z) > self.anomaly_zscore:
                anomalies.append({
                    'track_id': tid,
                    'velocity': round(float(v), 2),
                    'z_score': round(float(z), 2),
                    'type': 'fast_mover' if z > 0 else 'stationary',
                })
        return anomalies

    # ---- Flow Coherence ----

    def _flow_analysis(self, track_ids, track_history, centers):
        """
        Computes how uniformly everyone is moving in the same direction.
        coherence = 1.0 means everyone moving in exact same direction (stampede risk).
        coherence = 0.0 means random movement (normal crowd).
        """
        vectors = []
        flow_data = []

        for i, tid in enumerate(track_ids):
            hist = track_history.get(tid, [])
            if len(hist) < 2:
                continue

            # Average direction over recent history
            recent = hist[-min(self.coherence_window, len(hist)):]
            dx = recent[-1][0] - recent[0][0]
            dy = recent[-1][1] - recent[0][1]
            mag = np.sqrt(dx * dx + dy * dy)

            if mag > 2.0:  # ignore near-stationary
                norm_dx = dx / mag
                norm_dy = dy / mag
                vectors.append((norm_dx, norm_dy))
                flow_data.append({
                    'track_id': tid,
                    'cx': float(centers[i][0]),
                    'cy': float(centers[i][1]),
                    'dx': round(float(norm_dx), 3),
                    'dy': round(float(norm_dy), 3),
                    'magnitude': round(float(mag), 1),
                })

        if len(vectors) < 2:
            return 0.0, flow_data

        # Coherence = magnitude of mean unit vector
        # If all vectors point the same way, mean magnitude ~ 1.0
        # If random, mean magnitude ~ 0.0
        arr = np.array(vectors)
        mean_vec = arr.mean(axis=0)
        coherence = float(np.sqrt(mean_vec[0] ** 2 + mean_vec[1] ** 2))
        coherence = min(1.0, coherence)

        return coherence, flow_data

    # ---- Crowd Pressure ----

    def _crowd_pressure(self, centers, velocities, frame_shape):
        """
        Pressure = density * velocity_variance in local neighborhoods.
        Higher pressure = higher stampede/crush risk.
        """
        if len(centers) < 3:
            return 0.0

        h, w = frame_shape[:2]
        area = h * w
        if area == 0:
            return 0.0

        # Local density: average nearest-neighbor distance
        diffs = centers[:, np.newaxis, :] - centers[np.newaxis, :, :]
        dists = np.sqrt((diffs ** 2).sum(axis=2))
        np.fill_diagonal(dists, np.inf)
        min_dists = dists.min(axis=1)
        avg_min_dist = float(min_dists.mean())

        # Normalize: smaller distances = higher pressure
        # Reference: 50px nearest neighbor = pressure 1.0
        dist_pressure = max(0.0, 1.0 - (avg_min_dist / 200.0))

        # Velocity variance component
        vel_var = float(velocities.var()) if len(velocities) > 1 else 0.0
        vel_pressure = min(1.0, vel_var / 2.0)

        # Combined pressure
        pressure = 0.6 * dist_pressure + 0.4 * vel_pressure
        return min(1.0, pressure)

    # ---- Trend Prediction ----

    def _trend_prediction(self):
        """
        Exponential moving average prediction of where density/risk is heading.
        Returns prediction for next ~10 frames.
        """
        result = {
            'density_trend': 'stable',
            'risk_trend': 'stable',
            'density_ema': 0.0,
            'risk_ema': 0.0,
        }

        if len(self._density_history) < 5:
            return result

        # EMA with alpha=0.3
        density_ema = self._ema(list(self._density_history), 0.3)
        risk_ema = self._ema(list(self._risk_history), 0.3)

        # Compare current EMA to EMA from 5 steps ago
        if len(self._density_history) >= 10:
            old_density_ema = self._ema(list(self._density_history)[:-5], 0.3)
            density_delta = density_ema - old_density_ema
            if density_delta > 0.1:
                result['density_trend'] = 'increasing'
            elif density_delta < -0.1:
                result['density_trend'] = 'decreasing'

        if len(self._risk_history) >= 10:
            old_risk_ema = self._ema(list(self._risk_history)[:-5], 0.3)
            risk_delta = risk_ema - old_risk_ema
            if risk_delta > 0.03:
                result['risk_trend'] = 'increasing'
            elif risk_delta < -0.03:
                result['risk_trend'] = 'decreasing'

        result['density_ema'] = round(density_ema, 3)
        result['risk_ema'] = round(risk_ema, 3)
        return result

    @staticmethod
    def _ema(data, alpha):
        if not data:
            return 0.0
        ema = data[0]
        for val in data[1:]:
            ema = alpha * val + (1 - alpha) * ema
        return ema

    def _empty_result(self):
        return {
            'clusters': {'n_clusters': 0, 'labels': [], 'cluster_centers': [], 'cluster_sizes': []},
            'num_clusters': 0,
            'proximity_alerts': [],
            'anomalies': [],
            'flow_coherence': 0.0,
            'flow_vectors': [],
            'crowd_pressure': 0.0,
            'trend_prediction': self._trend_prediction(),
        }

class RiskCalculator:
    """Multi-factor risk scoring with ML-enhanced signals."""

    def __init__(self, config):
        self.config = config

    def calculate(self, density, avg_velocity, surge_rate, count,
                  crowd_pressure=0.0, flow_coherence=0.0):
        """
        Risk_Score = base weighted score + ML adjustments.

        Base: (w1 * density_norm) + (w2 * surge_norm) + (w3 * velocity_inverse_norm)
        ML boost: crowd_pressure and flow_coherence increase risk when elevated.

        Returns (risk_score 0-1, risk_level string).
        """
        # Normalize density: 0-1, max reference 10 people/m2
        density_norm = min(1.0, density / 10.0)

        # Normalize surge: 0-1, max reference 2 people/m2/s
        surge_norm = min(1.0, surge_rate / 2.0)

        # Inverse velocity normalize: lower velocity = higher risk
        # stagnant (< 0.2 m/s) = risk 1.0, normal (> 1.0 m/s) = risk 0.0
        if avg_velocity <= 0.2:
            velocity_inv_norm = 1.0
        elif avg_velocity >= 1.5:
            velocity_inv_norm = 0.0
        else:
            velocity_inv_norm = 1.0 - ((avg_velocity - 0.2) / 1.3)

        w1 = self.config.RISK_WEIGHT_DENSITY
        w2 = self.config.RISK_WEIGHT_SURGE
        w3 = self.config.RISK_WEIGHT_VELOCITY

        base_score = (w1 * density_norm) + (w2 * surge_norm) + (w3 * velocity_inv_norm)

        # ML-enhanced adjustments
        # Crowd pressure: high pressure (>0.5) boosts risk
        pressure_boost = max(0.0, crowd_pressure - 0.3) * 0.15

        # Flow coherence: high coherence (>0.6) means stampede-like movement
        coherence_boost = max(0.0, flow_coherence - 0.5) * 0.2

        risk_score = base_score + pressure_boost + coherence_boost

        # Boost for very large crowds
        if count > 100:
            risk_score = risk_score * 1.15

        risk_score = max(0.0, min(1.0, risk_score))

        # Classification: 0-25 SAFE, 25-50 CAUTION, 50-75 WARNING, 75-100 CRITICAL
        pct = risk_score * 100
        if pct >= 75:
            risk_level = 'CRITICAL'
        elif pct >= 50:
            risk_level = 'WARNING'
        elif pct >= 25:
            risk_level = 'CAUTION'
        else:
            risk_level = 'SAFE'

        return risk_score, risk_level

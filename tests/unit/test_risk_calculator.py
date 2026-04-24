"""RiskCalculator unit tests."""
from __future__ import annotations

import pytest

from backend.services.risk_calculator import RiskCalculator
from config import Config


@pytest.fixture
def calc():
    return RiskCalculator(Config)


class TestClassification:
    def test_empty_scene_is_safe(self, calc):
        score, level = calc.calculate(density=0.0, avg_velocity=1.0, surge_rate=0.0, count=0)
        assert level == 'SAFE'
        assert score < 0.25

    def test_critical_density_triggers_critical(self, calc):
        score, level = calc.calculate(
            density=10.0,
            avg_velocity=0.0,
            surge_rate=2.0,
            count=500,
        )
        assert level == 'CRITICAL'
        assert score >= 0.75

    def test_moderate_load_is_warning_or_caution(self, calc):
        score, level = calc.calculate(
            density=4.0,
            avg_velocity=0.3,
            surge_rate=0.5,
            count=80,
        )
        assert level in {'CAUTION', 'WARNING'}
        assert 0.25 <= score < 0.75


class TestVelocityInverse:
    def test_stagnant_velocity_boosts_risk(self, calc):
        stagnant_score, _ = calc.calculate(density=3.0, avg_velocity=0.1, surge_rate=0.0, count=50)
        fast_score, _ = calc.calculate(density=3.0, avg_velocity=2.0, surge_rate=0.0, count=50)
        assert stagnant_score > fast_score


class TestMLBoosts:
    def test_crowd_pressure_raises_score(self, calc):
        baseline, _ = calc.calculate(density=2.0, avg_velocity=0.5, surge_rate=0.0, count=30)
        boosted, _ = calc.calculate(
            density=2.0, avg_velocity=0.5, surge_rate=0.0, count=30,
            crowd_pressure=0.8,
        )
        assert boosted > baseline

    def test_large_crowd_amplifies_risk(self, calc):
        small, _ = calc.calculate(density=3.0, avg_velocity=0.3, surge_rate=0.5, count=50)
        large, _ = calc.calculate(density=3.0, avg_velocity=0.3, surge_rate=0.5, count=500)
        assert large > small


class TestClamping:
    def test_score_never_exceeds_one(self, calc):
        score, _ = calc.calculate(
            density=50.0,
            avg_velocity=0.0,
            surge_rate=20.0,
            count=10000,
            crowd_pressure=1.0,
            flow_coherence=1.0,
        )
        assert 0.0 <= score <= 1.0

    def test_score_never_below_zero(self, calc):
        score, _ = calc.calculate(
            density=-5.0,
            avg_velocity=100.0,
            surge_rate=-5.0,
            count=-10,
        )
        assert score >= 0.0

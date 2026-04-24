"""Alert hysteresis state machine.

Debounces risk-level flicker around threshold boundaries so we don't spam
operators with oscillating WARNING/SAFE transitions when the crowd metric
is bouncing between 49% and 51% risk. Exercised without touching the DB
or Flask app — we only test the pure state transitions.
"""
from __future__ import annotations

import pytest

from backend.services.alert_manager import AlertManager


class _Cfg:
    ALERT_HYSTERESIS_WARNING_ENTER = 3
    ALERT_HYSTERESIS_CRITICAL_ENTER = 1
    ALERT_HYSTERESIS_EXIT = 5


@pytest.fixture
def mgr():
    return AlertManager(_Cfg())


class TestWarningEscalation:
    def test_single_observation_does_not_escalate(self, mgr):
        assert mgr._apply_hysteresis('cam1', 'WARNING') == 'SAFE'

    def test_requires_n_consecutive_to_enter_warning(self, mgr):
        # enter = 3; first two stay SAFE, third trips
        assert mgr._apply_hysteresis('cam1', 'WARNING') == 'SAFE'
        assert mgr._apply_hysteresis('cam1', 'WARNING') == 'SAFE'
        assert mgr._apply_hysteresis('cam1', 'WARNING') == 'WARNING'

    def test_oscillation_never_trips_warning(self, mgr):
        """Classic flicker: one frame above, one below, repeat. Must stay SAFE."""
        for _ in range(10):
            mgr._apply_hysteresis('cam1', 'WARNING')
            mgr._apply_hysteresis('cam1', 'SAFE')
        assert mgr._hyst_state['cam1']['effective_level'] == 'SAFE'


class TestCriticalEscalation:
    def test_critical_enters_instantly(self, mgr):
        """Stampede signals (n_fallen>0, crush_risk>=0.6) are not flicker.
        First CRITICAL observation must promote immediately."""
        assert mgr._apply_hysteresis('cam1', 'CRITICAL') == 'CRITICAL'

    def test_critical_from_warning_also_instant(self, mgr):
        # Escalate to WARNING first
        for _ in range(3):
            mgr._apply_hysteresis('cam1', 'WARNING')
        assert mgr._apply_hysteresis('cam1', 'CRITICAL') == 'CRITICAL'


class TestDeescalation:
    def test_single_safe_does_not_demote_warning(self, mgr):
        for _ in range(3):
            mgr._apply_hysteresis('cam1', 'WARNING')
        assert mgr._apply_hysteresis('cam1', 'WARNING') == 'WARNING'
        # One SAFE tick must not flip back
        assert mgr._apply_hysteresis('cam1', 'SAFE') == 'WARNING'

    def test_requires_m_consecutive_to_exit(self, mgr):
        for _ in range(3):
            mgr._apply_hysteresis('cam1', 'WARNING')
        # Now at WARNING; need 5 SAFE frames to drop
        for _ in range(4):
            assert mgr._apply_hysteresis('cam1', 'SAFE') == 'WARNING'
        assert mgr._apply_hysteresis('cam1', 'SAFE') == 'SAFE'


class TestStatePerCamera:
    def test_state_is_per_camera(self, mgr):
        for _ in range(3):
            mgr._apply_hysteresis('cam-A', 'WARNING')
        # cam-B untouched
        assert mgr._apply_hysteresis('cam-B', 'SAFE') == 'SAFE'
        assert mgr._hyst_state['cam-A']['effective_level'] == 'WARNING'
        assert mgr._hyst_state['cam-B']['effective_level'] == 'SAFE'

    def test_reset_clears_state(self, mgr):
        for _ in range(3):
            mgr._apply_hysteresis('cam-A', 'WARNING')
        mgr.reset_hysteresis('cam-A')
        assert 'cam-A' not in mgr._hyst_state

    def test_reset_all_clears_everything(self, mgr):
        for _ in range(3):
            mgr._apply_hysteresis('cam-A', 'WARNING')
            mgr._apply_hysteresis('cam-B', 'WARNING')
        mgr.reset_hysteresis()
        assert mgr._hyst_state == {}

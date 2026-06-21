import time
from unittest.mock import patch
from cyber_traffic.state import StateMachine


def test_initial_state():
    sm = StateMachine()
    assert sm.current == "IDLE"


def test_idle_to_working():
    sm = StateMachine()
    changed = sm.transition("WORKING")
    assert changed is True
    assert sm.current == "WORKING"


def test_working_to_confirm():
    sm = StateMachine()
    sm.transition("WORKING")
    changed = sm.transition("CONFIRM")
    assert changed is True
    assert sm.current == "CONFIRM"


def test_confirm_to_working():
    sm = StateMachine()
    sm.transition("WORKING")
    sm.transition("CONFIRM")
    sm._last_confirm_time = 0  # force debounce to expire
    changed = sm.transition("WORKING")
    assert changed is True
    assert sm.current == "WORKING"


def test_any_to_error():
    sm = StateMachine()
    sm.transition("WORKING")
    changed = sm.transition("ERROR")
    assert changed is True
    assert sm.current == "ERROR"


def test_error_auto_recovery():
    sm = StateMachine()
    sm.transition("ERROR")
    with patch("cyber_traffic.state.time") as mock_time:
        mock_time.time.return_value = sm._error_since + 6
        recovered = sm.check_recovery()
    assert recovered is True
    assert sm.current == "IDLE"


def test_error_no_recovery_before_timeout():
    sm = StateMachine()
    sm.transition("ERROR")
    recovered = sm.check_recovery()
    assert recovered is False
    assert sm.current == "ERROR"


def test_working_dedup():
    """Consecutive WORKING events should not trigger a state change."""
    sm = StateMachine()
    sm.transition("WORKING")
    changed = sm.transition("WORKING")
    assert changed is False
    assert sm.current == "WORKING"


def test_confirm_debounce():
    """CONFIRM -> WORKING within debounce window should be rejected."""
    sm = StateMachine()
    sm.transition("WORKING")
    sm.transition("CONFIRM")
    # Try to transition back immediately — should be debounced
    changed = sm.transition("WORKING")
    assert changed is False
    assert sm.current == "CONFIRM"


def test_confirm_debounce_expired():
    """CONFIRM -> WORKING after debounce window should work."""
    sm = StateMachine()
    sm.transition("WORKING")
    sm.transition("CONFIRM")
    sm._last_confirm_time = 0  # force debounce to expire
    changed = sm.transition("WORKING")
    assert changed is True
    assert sm.current == "WORKING"


def test_state_history():
    sm = StateMachine()
    sm.transition("WORKING")
    sm.transition("CONFIRM")
    sm._last_confirm_time = 0  # force debounce to expire
    sm.transition("WORKING")
    sm.transition("IDLE")
    history = sm.get_history()
    assert len(history) == 4
    assert history[0]["state"] == "WORKING"
    assert history[-1]["state"] == "IDLE"


def test_detail_stored():
    sm = StateMachine()
    sm.transition("WORKING", detail="Reading file: main.py")
    assert sm.last_detail == "Reading file: main.py"

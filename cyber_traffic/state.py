"""State machine with debounce and auto-recovery."""
import time
import threading
from cyber_traffic.config import CONFIRM_DEBOUNCE, ERROR_RECOVERY, MAX_HISTORY


class StateMachine:
    def __init__(self):
        self._lock = threading.Lock()
        self._current = "IDLE"
        self._last_confirm_time = 0.0
        self._error_since = 0.0
        self._history = []
        self._last_detail = ""

    @property
    def current(self) -> str:
        return self._current

    @property
    def last_detail(self) -> str:
        return self._last_detail

    def transition(self, new_state: str, detail: str = "") -> bool:
        """Attempt a state transition. Returns True if state actually changed."""
        with self._lock:
            now = time.time()

            # Debounce: reject CONFIRM -> WORKING within debounce window
            if self._current == "CONFIRM" and new_state == "WORKING":
                if now - self._last_confirm_time < CONFIRM_DEBOUNCE:
                    return False

            # Dedup: same state is a no-op (except ERROR which can re-fire)
            if self._current == new_state and new_state != "ERROR":
                return False

            old = self._current
            self._current = new_state
            self._last_detail = detail or self._last_detail

            # Track CONFIRM timestamp for debounce
            if new_state == "CONFIRM":
                self._last_confirm_time = now

            # Track ERROR start for auto-recovery
            if new_state == "ERROR":
                self._error_since = now

            # Record history
            self._history.append({
                "state": new_state,
                "detail": self._last_detail,
                "timestamp": now,
            })
            if len(self._history) > MAX_HISTORY:
                self._history = self._history[-MAX_HISTORY:]

            return True

    def check_recovery(self) -> bool:
        """Check if ERROR state should auto-recover to IDLE. Returns True if recovered."""
        with self._lock:
            if self._current != "ERROR":
                return False
            if time.time() - self._error_since >= ERROR_RECOVERY:
                self._current = "IDLE"
                self._history.append({
                    "state": "IDLE",
                    "detail": "自动恢复",
                    "timestamp": time.time(),
                })
                return True
            return False

    def get_history(self) -> list:
        """Return a copy of the state history."""
        with self._lock:
            return list(self._history)

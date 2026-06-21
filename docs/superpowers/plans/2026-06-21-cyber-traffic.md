# Cyber Traffic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a macOS menu bar app that shows Claude Code's real-time status as a traffic light (green=idle, yellow=working, blinking yellow=needs confirmation, red=error).

**Architecture:** A rumps menu bar app listens on a Unix socket. Claude Code hook scripts send state updates through the socket. A state machine with debounce logic drives icon updates, sound playback, and history logging.

**Tech Stack:** Python 3, rumps (menu bar), Unix socket (IPC), macOS system sounds (afplay), setuptools (packaging)

---

## File Map

```
cyber-traffic/
├── README.md                                    # Usage docs
├── requirements.txt                             # rumps
├── setup.py                                     # Package + entry points
├── tests/
│   ├── __init__.py
│   ├── test_state.py                            # State machine unit tests
│   ├── test_server.py                           # Socket server tests
│   ├── test_sound.py                            # Sound player tests
│   └── test_hook.py                             # Hook script tests
├── cyber_traffic/
│   ├── __init__.py
│   ├── config.py                                # Constants (socket path, colors, etc.)
│   ├── state.py                                 # StateMachine class
│   ├── server.py                                # Unix socket server thread
│   ├── sound.py                                 # Sound playback via afplay
│   ├── icons.py                                 # Icon data (colored circles)
│   ├── app.py                                   # rumps.App main entry
│   └── setup_hooks.py                           # --setup: auto-configure hooks
└── hooks/
    ├── notify_traffic.py                        # Hook script called by Claude Code
    └── README.md                                # Manual hook config instructions
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `setup.py`
- Create: `cyber_traffic/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
rumps>=0.4.0
```

- [ ] **Step 2: Create setup.py**

```python
from setuptools import setup, find_packages

setup(
    name="cyber-traffic",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["rumps>=0.4.0"],
    entry_points={
        "console_scripts": [
            "cyber-traffic=cyber_traffic.app:main",
        ],
    },
    python_requires=">=3.9",
)
```

- [ ] **Step 3: Create package init files**

`cyber_traffic/__init__.py`:
```python
"""Cyber Traffic — Claude Code 红绿灯状态指示器"""
__version__ = "0.1.0"
```

`tests/__init__.py`:
```python
```

- [ ] **Step 4: Install in dev mode and verify**

Run:
```bash
cd /Volumes/Fanxiang/workspace/cyber-traffic && pip install -e ".[dev]" 2>&1 | tail -3
python -c "import cyber_traffic; print(cyber_traffic.__version__)"
```

Expected: `0.1.0`

- [ ] **Step 5: Commit**

```bash
git init && git add -A && git commit -m "chore: project scaffolding"
```

---

### Task 2: Config Module

**Files:**
- Create: `cyber_traffic/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing test**

`tests/test_config.py`:
```python
from cyber_traffic.config import SOCKET_PATH, SOUNDS, ICONS


def test_socket_path_is_string():
    assert isinstance(SOCKET_PATH, str)
    assert SOCKET_PATH.endswith(".sock")


def test_sounds_has_all_states():
    assert set(SOUNDS.keys()) == {"CONFIRM", "ERROR", "IDLE_FROM_WORKING"}


def test_sounds_are_valid_paths():
    import os
    for name, path in SOUNDS.items():
        assert os.path.exists(path), f"Sound not found: {name} -> {path}"


def test_icons_has_all_states():
    assert set(ICONS.keys()) == {"IDLE", "WORKING", "CONFIRM", "ERROR"}
    for state, icon in ICONS.items():
        assert isinstance(icon, str)
        assert len(icon) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'cyber_traffic.config'`

- [ ] **Step 3: Write config module**

`cyber_traffic/config.py`:
```python
"""App-wide constants."""
import os

# Socket
SOCKET_PATH = "/tmp/claude-traffic.sock"

# macOS system sounds (no extension — afplay resolves .aiff)
SOUND_DIR = "/System/Library/Sounds"
SOUNDS = {
    "CONFIRM": os.path.join(SOUND_DIR, "Glass.aiff"),
    "ERROR": os.path.join(SOUND_DIR, "Basso.aiff"),
    "IDLE_FROM_WORKING": os.path.join(SOUND_DIR, "Hero.aiff"),
}

# Menu bar icon characters (Unicode filled circle)
ICONS = {
    "IDLE": "●",       # ● green
    "WORKING": "●",    # ● yellow
    "CONFIRM": "●",    # ● yellow (blink)
    "ERROR": "●",      # ● red
}

# Icon colors (rumps uses NSColor via PyObjC)
COLORS = {
    "IDLE": (52, 199, 89),      # #34C759
    "WORKING": (255, 204, 0),   # #FFCC00
    "CONFIRM": (255, 204, 0),   # #FFCC00
    "ERROR": (255, 59, 48),     # #FF3B30
}

# Blink interval for CONFIRM state (seconds)
BLINK_INTERVAL = 0.5

# Debounce: minimum seconds between CONFIRM -> WORKING transitions
CONFIRM_DEBOUNCE = 2.0

# Auto-recover ERROR to IDLE after this many seconds
ERROR_RECOVERY = 5.0

# Max history entries shown in dropdown
MAX_HISTORY = 20
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_config.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add cyber_traffic/config.py tests/test_config.py
git commit -m "feat: config module with constants"
```

---

### Task 3: State Machine

**Files:**
- Create: `cyber_traffic/state.py`
- Create: `tests/test_state.py`

- [ ] **Step 1: Write failing tests**

`tests/test_state.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_state.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write state machine**

`cyber_traffic/state.py`:
```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_state.py -v`
Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add cyber_traffic/state.py tests/test_state.py
git commit -m "feat: state machine with debounce and auto-recovery"
```

---

### Task 4: Socket Server

**Files:**
- Create: `cyber_traffic/server.py`
- Create: `tests/test_server.py`

- [ ] **Step 1: Write failing tests**

`tests/test_server.py`:
```python
import json
import socket
import time
import threading
from unittest.mock import MagicMock
from cyber_traffic.server import SocketServer
from cyber_traffic.config import SOCKET_PATH


def test_server_receives_message(tmp_path):
    sock_path = str(tmp_path / "test.sock")
    callback = MagicMock()
    server = SocketServer(sock_path, callback)
    server.start()
    time.sleep(0.1)  # let server bind

    # Send a message
    msg = json.dumps({"state": "WORKING", "detail": "test", "timestamp": 0})
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(sock_path)
    client.sendall(msg.encode())
    client.close()
    time.sleep(0.2)  # let server process

    callback.assert_called_once()
    received = callback.call_args[0][0]
    assert received["state"] == "WORKING"
    assert received["detail"] == "test"

    server.stop()


def test_server_handles_malformed_json(tmp_path):
    sock_path = str(tmp_path / "test.sock")
    callback = MagicMock()
    server = SocketServer(sock_path, callback)
    server.start()
    time.sleep(0.1)

    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(sock_path)
    client.sendall(b"not json{{{")
    client.close()
    time.sleep(0.2)

    # Should not crash, callback not called for bad data
    callback.assert_not_called()
    server.stop()


def test_server_multiple_messages(tmp_path):
    sock_path = str(tmp_path / "test.sock")
    callback = MagicMock()
    server = SocketServer(sock_path, callback)
    server.start()
    time.sleep(0.1)

    for state in ["WORKING", "CONFIRM", "IDLE"]:
        msg = json.dumps({"state": state, "detail": "", "timestamp": 0})
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(sock_path)
        client.sendall(msg.encode())
        client.close()
        time.sleep(0.1)

    time.sleep(0.3)
    assert callback.call_count == 3
    server.stop()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_server.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write socket server**

`cyber_traffic/server.py`:
```python
"""Unix socket server — listens for state updates from hook scripts."""
import json
import os
import socket
import threading
import logging

logger = logging.getLogger(__name__)


class SocketServer:
    def __init__(self, sock_path: str, on_message):
        self._sock_path = sock_path
        self._on_message = on_message
        self._server_sock = None
        self._thread = None
        self._running = False

    def start(self):
        """Start the server in a background thread."""
        # Clean up stale socket file
        if os.path.exists(self._sock_path):
            os.unlink(self._sock_path)

        self._server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._server_sock.bind(self._sock_path)
        self._server_sock.listen(5)
        self._server_sock.settimeout(1.0)  # allow periodic stop checks
        self._running = True

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while self._running:
            try:
                conn, _ = self._server_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                self._handle_connection(conn)
            except Exception as e:
                logger.error("Error handling connection: %s", e)
            finally:
                conn.close()

    def _handle_connection(self, conn):
        data = b""
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
        if not data:
            return
        try:
            msg = json.loads(data.decode())
            self._on_message(msg)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning("Malformed message ignored: %s", e)

    def stop(self):
        """Stop the server and clean up."""
        self._running = False
        if self._server_sock:
            self._server_sock.close()
        if self._thread:
            self._thread.join(timeout=3)
        if os.path.exists(self._sock_path):
            os.unlink(self._sock_path)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_server.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add cyber_traffic/server.py tests/test_server.py
git commit -m "feat: Unix socket server for receiving state updates"
```

---

### Task 5: Sound Player

**Files:**
- Create: `cyber_traffic/sound.py`
- Create: `tests/test_sound.py`

- [ ] **Step 1: Write failing tests**

`tests/test_sound.py`:
```python
from unittest.mock import patch, MagicMock
from cyber_traffic.sound import SoundPlayer


def test_play_calls_afplay():
    player = SoundPlayer(muted=False)
    with patch("subprocess.run") as mock_run:
        player.play("Glass.aiff")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "afplay"
        assert "Glass.aiff" in args[1]


def test_muted_does_not_play():
    player = SoundPlayer(muted=True)
    with patch("subprocess.run") as mock_run:
        player.play("Glass.aiff")
        mock_run.assert_not_called()


def test_toggle_mute():
    player = SoundPlayer(muted=False)
    assert player.muted is False
    player.toggle_mute()
    assert player.muted is True
    player.toggle_mute()
    assert player.muted is False


def test_play_for_state_change_working():
    """WORKING state should not trigger any sound."""
    player = SoundPlayer(muted=False)
    with patch("subprocess.run") as mock_run:
        player.play_for_transition("IDLE", "WORKING")
        mock_run.assert_not_called()


def test_play_for_state_change_confirm():
    player = SoundPlayer(muted=False)
    with patch("subprocess.run") as mock_run:
        player.play_for_transition("WORKING", "CONFIRM")
        mock_run.assert_called_once()


def test_play_for_state_change_error():
    player = SoundPlayer(muted=False)
    with patch("subprocess.run") as mock_run:
        player.play_for_transition("WORKING", "ERROR")
        mock_run.assert_called_once()


def test_play_for_state_change_idle_from_working():
    player = SoundPlayer(muted=False)
    with patch("subprocess.run") as mock_run:
        player.play_for_transition("WORKING", "IDLE")
        mock_run.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_sound.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write sound player**

`cyber_traffic/sound.py`:
```python
"""Sound playback using macOS system sounds via afplay."""
import subprocess
import logging
from cyber_traffic.config import SOUNDS

logger = logging.getLogger(__name__)

# Map (old_state, new_state) -> sound key
_TRANSITION_SOUNDS = {
    ("WORKING", "CONFIRM"): "CONFIRM",
    ("CONFIRM", "WORKING"): "CONFIRM",  # re-use Glass as "confirmed"
    ("*", "ERROR"): "ERROR",
    ("*", "IDLE"): "IDLE_FROM_WORKING",
}


class SoundPlayer:
    def __init__(self, muted: bool = False):
        self.muted = muted

    def toggle_mute(self):
        self.muted = not self.muted

    def play(self, sound_path: str):
        """Play a sound file using afplay."""
        if self.muted:
            return
        try:
            subprocess.run(["afplay", sound_path], timeout=5, check=False)
        except Exception as e:
            logger.warning("Failed to play sound: %s", e)

    def play_for_transition(self, old_state: str, new_state: str):
        """Play the appropriate sound for a state transition."""
        key = (old_state, new_state)
        sound_key = _TRANSITION_SOUNDS.get(key)
        if sound_key is None:
            # Try wildcard match for new_state
            sound_key = _TRANSITION_SOUNDS.get(("*", new_state))
        if sound_key and sound_key in SOUNDS:
            self.play(SOUNDS[sound_key])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_sound.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add cyber_traffic/sound.py tests/test_sound.py
git commit -m "feat: sound player with transition-based playback"
```

---

### Task 6: Icon Rendering

**Files:**
- Create: `cyber_traffic/icons.py`

- [ ] **Step 1: Write icon module**

`cyber_traffic/icons.py`:
```python
"""Menu bar icon rendering with color support via rumps/PyObjC."""
import rumps
from cyber_traffic.config import COLORS, ICONS


def _make_colored_icon(char: str, rgb: tuple) -> rumps.MenuItem:
    """Create an attributed title string for menu bar display."""
    # rumps supports NSAttributedTitle via PyObjC
    from AppKit import NSColor, NSFont, NSAttributedString, NSMutableAttributedString
    r, g, b = rgb
    color = NSColor.colorWithCalibratedRed_green_blue_alpha_(r / 255, g / 255, b / 255, 1.0)
    font = NSFont.systemFontOfSize_(14.0)
    attrs = {
        "NSColor": color,
        "NSFont": font,
    }
    return NSAttributedString.alloc().initWithString_attributes_(char, attrs)


# Pre-render all icons at import time
ICONS_RENDERED = {}
for _state in ("IDLE", "WORKING", "CONFIRM", "ERROR"):
    ICONS_RENDERED[_state] = _make_colored_icon(ICONS[_state], COLORS[_state])


def get_icon(state: str):
    """Return the rendered icon for a given state."""
    return ICONS_RENDERED.get(state, ICONS_RENDERED["IDLE"])
```

- [ ] **Step 2: Verify import works**

Run: `python -c "from cyber_traffic.icons import ICONS_RENDERED; print(list(ICONS_RENDERED.keys()))"`
Expected: `['IDLE', 'WORKING', 'CONFIRM', 'ERROR']`

- [ ] **Step 3: Commit**

```bash
git add cyber_traffic/icons.py
git commit -m "feat: colored menu bar icon rendering"
```

---

### Task 7: Main App (rumps)

**Files:**
- Create: `cyber_traffic/app.py`
- Modify: `cyber_traffic/config.py` (add `APP_NAME`)

- [ ] **Step 1: Write main app**

`cyber_traffic/app.py`:
```python
"""Main menu bar app — integrates all components."""
import sys
import threading
import rumps
from cyber_traffic.config import SOCKET_PATH, BLINK_INTERVAL, APP_NAME
from cyber_traffic.state import StateMachine
from cyber_traffic.server import SocketServer
from cyber_traffic.sound import SoundPlayer
from cyber_traffic.icons import get_icon


class TrafficApp(rumps.App):
    def __init__(self):
        super().__init__(name=APP_NAME, title="●")  # default green dot
        self._state = StateMachine()
        self._sound = SoundPlayer()
        self._blink_timer = None
        self._blink_visible = True
        self._server = SocketServer(SOCKET_PATH, self._on_message)
        self._server.start()

        # Build dropdown menu
        self._status_item = rumps.MenuItem("当前状态：空闲")
        self._history_menu = rumps.MenuItem("状态历史")
        self._mute_item = rumps.MenuItem("🔇 静音", callback=self._toggle_mute)
        self.menu = [
            self._status_item,
            self._history_menu,
            None,  # separator
            self._mute_item,
            rumps.MenuItem("退出", callback=self._quit),
        ]

        # Recovery timer (checks ERROR -> IDLE auto-recovery)
        rumps.Timer(self._check_recovery, 1.0).start()

        # Set initial icon
        self._update_icon("IDLE")

    def _on_message(self, msg: dict):
        """Called by socket server thread when a message arrives."""
        new_state = msg.get("state", "IDLE")
        detail = msg.get("detail", "")
        old_state = self._state.current

        changed = self._state.transition(new_state, detail=detail)
        if changed:
            # Update UI on main thread
            rumps.Timer(self._apply_state_change, 0.01).start()

    def _apply_state_change(self, timer):
        """One-shot timer callback to apply state change on main thread."""
        timer.stop()
        state = self._state.current
        self._update_icon(state)
        self._update_menu()
        old = self._state._history[-2]["state"] if len(self._state._history) >= 2 else "IDLE"
        self._sound.play_for_transition(old, state)

    def _update_icon(self, state: str):
        """Update the menu bar icon and manage blinking."""
        # Stop any existing blink
        if self._blink_timer:
            self._blink_timer.stop()
            self._blink_timer = None

        if state == "CONFIRM":
            self._start_blink()
        else:
            self.title = get_icon(state)

        # Update status text
        labels = {"IDLE": "空闲", "WORKING": "工作中", "CONFIRM": "等待确认", "ERROR": "错误"}
        self._status_item.title = f"当前状态：{labels.get(state, state)}"

    def _start_blink(self):
        """Start blinking animation for CONFIRM state."""
        self._blink_visible = True
        self._blink_timer = rumps.Timer(self._blink_tick, BLINK_INTERVAL)
        self._blink_timer.start()

    def _blink_tick(self, timer):
        """Blink timer callback — toggles icon visibility."""
        if self._state.current != "CONFIRM":
            timer.stop()
            self._blink_timer = None
            self.title = get_icon(self._state.current)
            return
        self._blink_visible = not self._blink_visible
        if self._blink_visible:
            self.title = get_icon("CONFIRM")
        else:
            self.title = ""  # invisible frame

    def _update_menu(self):
        """Refresh the history submenu."""
        history = self._state.get_history()
        labels = {"IDLE": "🟢 空闲", "WORKING": "🟡 工作中", "CONFIRM": "🟡 等待确认", "ERROR": "🔴 错误"}
        self._history_menu.clear()
        for entry in reversed(history[-10:]):  # show last 10
            import datetime
            ts = datetime.datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M:%S")
            label = labels.get(entry["state"], entry["state"])
            detail = entry.get("detail", "")
            text = f"{label}"
            if detail:
                text += f" — {detail}"
            item = rumps.MenuItem(f"{text}  {ts}")
            self._history_menu.add(item)

    def _check_recovery(self, timer):
        """Periodic check for ERROR auto-recovery."""
        if self._state.check_recovery():
            self._update_icon("IDLE")
            self._update_menu()
            self._sound.play_for_transition("ERROR", "IDLE")

    def _toggle_mute(self, _):
        self._sound.toggle_mute()
        self._mute_item.title = "🔊 取消静音" if self._sound.muted else "🔇 静音"

    def _quit(self, _):
        self._server.stop()
        rumps.quit_application()


def main():
    if "--setup" in sys.argv:
        from cyber_traffic.setup_hooks import setup
        setup()
        return
    TrafficApp().run()
```

- [ ] **Step 2: Add APP_NAME to config**

Add to `cyber_traffic/config.py`:
```python
APP_NAME = "Cyber Traffic"
```

- [ ] **Step 3: Verify app starts (manual test)**

Run: `cyber-traffic`
Expected: Menu bar shows green dot. Press Ctrl+C to stop.

- [ ] **Step 4: Commit**

```bash
git add cyber_traffic/app.py cyber_traffic/config.py
git commit -m "feat: main rumps app with icon, history, and sound"
```

---

### Task 8: Hook Script

**Files:**
- Create: `hooks/notify_traffic.py`
- Create: `tests/test_hook.py`

- [ ] **Step 1: Write failing tests**

`tests/test_hook.py`:
```python
import json
import socket
import threading
import time
from unittest.mock import patch
from hooks import notify_traffic as hook


def test_map_event_pretooluse_no_permission():
    event = {"type": "PreToolUse", "tool": {"name": "Read"}}
    state, detail = hook.map_event(event)
    assert state == "WORKING"
    assert "Read" in detail


def test_map_event_pretooluse_with_permission():
    event = {"type": "PreToolUse", "tool": {"name": "Write"}, "permission_required": True}
    state, detail = hook.map_event(event)
    assert state == "CONFIRM"
    assert "Write" in detail


def test_map_event_stop():
    event = {"type": "Stop"}
    state, detail = hook.map_event(event)
    assert state == "IDLE"


def test_map_event_notification_error():
    event = {"type": "Notification", "message": "Error: something failed"}
    state, detail = hook.map_event(event)
    assert state == "ERROR"


def test_map_event_notification_normal():
    event = {"type": "Notification", "message": "Task complete"}
    state, detail = hook.map_event(event)
    assert state == "WORKING"


def test_send_state(tmp_path):
    sock_path = str(tmp_path / "test.sock")
    received = []

    def server_thread():
        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(sock_path)
        srv.listen(1)
        srv.settimeout(2)
        conn, _ = srv.accept()
        data = conn.recv(4096)
        received.append(json.loads(data.decode()))
        conn.close()
        srv.close()

    t = threading.Thread(target=server_thread)
    t.start()
    time.sleep(0.1)

    hook.send_state("WORKING", "test", sock_path=sock_path)
    t.join(timeout=3)

    assert len(received) == 1
    assert received[0]["state"] == "WORKING"
    assert received[0]["detail"] == "test"


def test_send_state_no_server():
    """Should not crash if server is not running."""
    hook.send_state("IDLE", "test", sock_path="/tmp/nonexistent-traffic-test.sock")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_hook.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write hook script**

`hooks/__init__.py`:
```python
```

`hooks/notify_traffic.py`:
```python
#!/usr/bin/env python3
"""Claude Code hook script — sends state updates to Cyber Traffic via Unix socket."""
import json
import socket
import sys
import time

# Allow overriding socket path for testing
SOCKET_PATH = "/tmp/claude-traffic.sock"


def map_event(event: dict) -> tuple:
    """Map a Claude Code hook event to (state, detail).

    Returns:
        (state, detail) tuple
    """
    event_type = event.get("type", "")

    if event_type == "PreToolUse":
        tool_name = event.get("tool", {}).get("name", "unknown")
        if event.get("permission_required"):
            return ("CONFIRM", f"需要确认: {tool_name}")
        return ("WORKING", f"执行: {tool_name}")

    if event_type == "PostToolUse":
        tool_name = event.get("tool", {}).get("name", "unknown")
        return ("WORKING", f"完成: {tool_name}")

    if event_type == "Stop":
        return ("IDLE", "完成")

    if event_type == "Notification":
        msg = event.get("message", "")
        if "error" in msg.lower() or "Error" in msg:
            return ("ERROR", msg)
        return ("WORKING", msg)

    return ("WORKING", f"未知事件: {event_type}")


def send_state(state: str, detail: str = "", sock_path: str = None):
    """Send a state update message to the Cyber Traffic app via Unix socket."""
    path = sock_path or SOCKET_PATH
    msg = json.dumps({
        "state": state,
        "detail": detail,
        "timestamp": int(time.time()),
    })
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(path)
        sock.sendall(msg.encode())
        sock.close()
    except (ConnectionRefusedError, FileNotFoundError, OSError):
        # App not running — silently ignore
        pass


def main():
    """Entry point — read event from stdin, map, and send."""
    try:
        raw = sys.stdin.read()
        event = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return

    state, detail = map_event(event)
    send_state(state, detail)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_hook.py -v`
Expected: 7 passed

- [ ] **Step 5: Make hook script executable**

Run: `chmod +x hooks/notify_traffic.py`

- [ ] **Step 6: Commit**

```bash
git add hooks/ tests/test_hook.py
git commit -m "feat: hook script for Claude Code integration"
```

---

### Task 9: Setup Command

**Files:**
- Create: `cyber_traffic/setup_hooks.py`

- [ ] **Step 1: Write setup module**

`cyber_traffic/setup_hooks.py`:
```python
"""Auto-configure Claude Code hooks in ~/.claude/settings.json."""
import json
import os
import sys


def get_hook_command() -> str:
    """Get the absolute path to the hook script."""
    # Resolve relative to the package root
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hook_path = os.path.join(pkg_dir, "hooks", "notify_traffic.py")
    return f"python3 {hook_path}"


def setup():
    """Add Cyber Traffic hooks to ~/.claude/settings.json."""
    settings_path = os.path.expanduser("~/.claude/settings.json")

    # Read existing settings
    settings = {}
    if os.path.exists(settings_path):
        with open(settings_path, "r") as f:
            settings = json.load(f)

    # Ensure hooks key exists
    if "hooks" not in settings:
        settings["hooks"] = {}

    hook_cmd = get_hook_command()
    hook_entry = [{"type": "command", "command": hook_cmd}]

    # Add hooks (don't duplicate)
    for hook_name in ("PreToolUse", "Stop", "Notification"):
        existing = settings["hooks"].get(hook_name, [])
        # Check if our hook is already configured
        if not any(e.get("command") == hook_cmd for e in existing):
            existing.append(hook_entry[0])
            settings["hooks"][hook_name] = existing

    # Write back
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"✅ Hooks configured in {settings_path}")
    print(f"   Hook command: {hook_cmd}")
    print(f"   Hooks: PreToolUse, Stop, Notification")
    print()
    print("Restart Claude Code to activate the hooks.")
```

- [ ] **Step 2: Verify setup module is importable**

Run: `python -c "from cyber_traffic.setup_hooks import get_hook_command; print(get_hook_command())"`
Expected: prints absolute path to `hooks/notify_traffic.py`

- [ ] **Step 3: Commit**

```bash
git add cyber_traffic/setup_hooks.py
git commit -m "feat: --setup command for auto-configuring hooks"
```

---

### Task 10: README + Final Polish

**Files:**
- Create: `README.md`
- Create: `hooks/README.md`

- [ ] **Step 1: Write README.md**

```markdown
# 🚦 Cyber Traffic

Claude Code 红绿灯状态指示器 — macOS 菜单栏版本。

## 效果

菜单栏显示彩色圆点，实时反映 Claude Code 的状态：

| 图标 | 状态 | 含义 |
|------|------|------|
| 🟢 | 空闲 | Claude 等待输入 |
| 🟡 | 工作中 | Claude 正在思考/执行 |
| 🟡 闪烁 | 等待确认 | 需要你批准操作 |
| 🔴 | 错误 | 出错或被阻塞 |

## 安装

```bash
pip install -e .
```

## 使用

```bash
# 启动菜单栏 app
cyber-traffic

# 自动配置 Claude Code hooks
cyber-traffic --setup
```

`--setup` 会自动修改 `~/.claude/settings.json`，添加 hook 配置。配置完成后重启 Claude Code 即可生效。

## 功能

- ✅ 实时状态指示（绿/黄/红）
- ✅ 闪烁黄灯 = 等待确认
- ✅ 状态变化音效（可静音）
- ✅ 状态历史时间线
- ✅ 错误状态自动恢复（5秒）
- ✅ 一键配置 Claude Code hooks

## 卸载 Hook

编辑 `~/.claude/settings.json`，删除 `hooks` 中包含 `notify_traffic` 的条目。
```

- [ ] **Step 2: Write hooks/README.md**

```markdown
# Hook 配置说明

## 自动配置（推荐）

```bash
cyber-traffic --setup
```

## 手动配置

编辑 `~/.claude/settings.json`，添加以下内容：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "python3 /absolute/path/to/hooks/notify_traffic.py"
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "python3 /absolute/path/to/hooks/notify_traffic.py"
      }
    ],
    "Notification": [
      {
        "type": "command",
        "command": "python3 /absolute/path/to/hooks/notify_traffic.py"
      }
    ]
  }
}
```

将 `/absolute/path/to/` 替换为实际路径。
```

- [ ] **Step 3: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: All tests pass

- [ ] **Step 4: Final commit**

```bash
git add README.md hooks/README.md
git commit -m "docs: README and hook configuration guide"
```

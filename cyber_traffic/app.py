"""Main menu bar app — integrates all components."""
import sys
import datetime
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

    def _set_attributed_title(self, attributed_str):
        """Set an NSAttributedString on the menu bar button."""
        try:
            self._nsapp.nsstatusitem.button().setAttributedTitle_(attributed_str)
        except AttributeError:
            # Fallback before _nsapp is initialized
            self.title = "●"

    def _on_message(self, msg: dict):
        """Called by socket server thread when a message arrives."""
        new_state = msg.get("state", "IDLE")
        detail = msg.get("detail", "")

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
            self._set_attributed_title(get_icon(state))

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
            self._set_attributed_title(get_icon(self._state.current))
            return
        self._blink_visible = not self._blink_visible
        if self._blink_visible:
            self._set_attributed_title(get_icon("CONFIRM"))
        else:
            self.title = ""  # invisible frame

    def _update_menu(self):
        """Refresh the history submenu."""
        history = self._state.get_history()
        labels = {"IDLE": "🟢 空闲", "WORKING": "🟡 工作中", "CONFIRM": "🟡 等待确认", "ERROR": "🔴 错误"}
        self._history_menu.clear()
        for entry in reversed(history[-10:]):  # show last 10
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

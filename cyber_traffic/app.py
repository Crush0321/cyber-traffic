"""Main menu bar app — integrates all components."""
import os
import sys
import datetime
import threading
import rumps
from cyber_traffic.config import SOCKET_PATH, BLINK_INTERVAL, APP_NAME
from cyber_traffic.state import StateMachine
from cyber_traffic.server import SocketServer
from cyber_traffic.sound import SoundPlayer
from cyber_traffic.icons import get_icon


class TrafficApp(rumps.App):
    def __init__(self):
        super().__init__(name=APP_NAME, title="●", quit_button=None)  # disable default Quit
        self._state = StateMachine()
        self._sound = SoundPlayer()
        self._blink_timer = None
        self._blink_visible = True
        self._pending_update = False
        self._lock = threading.Lock()
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

        # Main update timer — checks for pending state changes every 100ms
        rumps.Timer(self._tick, 0.1).start()

    def _tick(self, timer):
        """Periodic tick — applies pending state changes on main thread."""
        # Check ERROR auto-recovery
        if self._state.check_recovery():
            self._update_icon("IDLE")
            self._update_menu()
            self._sound.play_for_transition("ERROR", "IDLE")
            return

        with self._lock:
            if not self._pending_update:
                return
            self._pending_update = False

        state = self._state.current
        self._update_icon(state)
        self._update_menu()
        old = self._state._history[-2]["state"] if len(self._state._history) >= 2 else "IDLE"
        self._sound.play_for_transition(old, state)

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
            with self._lock:
                self._pending_update = True

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
        try:
            self._history_menu.clear()
        except AttributeError:
            return  # menu not yet initialized
        for entry in reversed(history[-10:]):  # show last 10
            ts = datetime.datetime.fromtimestamp(entry["timestamp"]).strftime("%H:%M:%S")
            label = labels.get(entry["state"], entry["state"])
            detail = entry.get("detail", "")
            text = f"{label}"
            if detail:
                text += f" — {detail}"
            item = rumps.MenuItem(f"{text}  {ts}")
            self._history_menu.add(item)

    def _toggle_mute(self, _):
        self._sound.toggle_mute()
        self._mute_item.title = "🔊 取消静音" if self._sound.muted else "🔇 静音"

    def _quit(self, _):
        self._server.stop()
        rumps.quit_application()


def _install_launchd():
    """Install launchd plist for auto-start on login."""
    import shutil
    plist_src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "com.crush.cyber-traffic.plist")
    plist_dst = os.path.expanduser("~/Library/LaunchAgents/com.crush.cyber-traffic.plist")

    if not os.path.exists(plist_src):
        print(f"❌ Plist not found: {plist_src}")
        return

    os.makedirs(os.path.dirname(plist_dst), exist_ok=True)
    shutil.copy2(plist_src, plist_dst)
    os.system(f"launchctl load {plist_dst}")
    print(f"✅ 已安装开机自启: {plist_dst}")
    print("   登录后自动启动，崩溃后自动重启")
    print(f"   日志: /tmp/cyber-traffic.log")


def _uninstall_launchd():
    """Uninstall launchd plist."""
    plist_dst = os.path.expanduser("~/Library/LaunchAgents/com.crush.cyber-traffic.plist")
    if os.path.exists(plist_dst):
        os.system(f"launchctl unload {plist_dst}")
        os.remove(plist_dst)
        print(f"✅ 已卸载开机自启: {plist_dst}")
    else:
        print("ℹ️  未安装开机自启")


def main():
    if "--setup" in sys.argv:
        from cyber_traffic.setup_hooks import setup
        setup()
        return
    if "--install" in sys.argv:
        _install_launchd()
        return
    if "--uninstall" in sys.argv:
        _uninstall_launchd()
        return
    TrafficApp().run()

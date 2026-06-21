#!/usr/bin/env python3
"""Claude Code hook script -- sends state updates to Cyber Traffic via Unix socket."""
import json
import socket
import sys
import time

# Allow overriding socket path for testing
SOCKET_PATH = "/tmp/claude-traffic.sock"


def map_event(event: dict) -> tuple:
    """Map a Claude Code hook event to (state, detail).

    Supports both old format (type/tool.name) and new format (hook_event_name/tool_name).

    Returns:
        (state, detail) tuple
    """
    # Support both old and new field names
    event_type = event.get("hook_event_name") or event.get("type", "")
    tool_name = event.get("tool_name") or event.get("tool", {}).get("name", "unknown")

    if event_type == "PreToolUse":
        # New format uses permission_mode, old uses permission_required
        needs_permission = (
            event.get("permission_mode") == "ask"
            or event.get("permission_required")
        )
        if needs_permission:
            return ("CONFIRM", f"需要确认: {tool_name}")
        return ("WORKING", f"执行: {tool_name}")

    if event_type == "PostToolUse":
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
        # App not running -- silently ignore
        pass


def main():
    """Entry point -- read event from stdin, map, and send."""
    try:
        raw = sys.stdin.read()
        event = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return

    state, detail = map_event(event)
    send_state(state, detail)


if __name__ == "__main__":
    main()

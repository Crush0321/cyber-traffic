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


def test_send_state():
    # tmp_path on macOS generates paths exceeding the 104-char Unix socket limit
    sock_path = "/tmp/t_hook_test.sock"
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

    try:
        hook.send_state("WORKING", "test", sock_path=sock_path)
        t.join(timeout=3)

        assert len(received) == 1
        assert received[0]["state"] == "WORKING"
        assert received[0]["detail"] == "test"
    finally:
        import os
        if os.path.exists(sock_path):
            os.unlink(sock_path)


def test_send_state_no_server():
    """Should not crash if server is not running."""
    hook.send_state("IDLE", "test", sock_path="/tmp/nonexistent-traffic-test.sock")

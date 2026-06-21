import json
import os
import socket
import time
import threading
import tempfile
import uuid
from unittest.mock import MagicMock
from cyber_traffic.server import SocketServer
from cyber_traffic.config import SOCKET_PATH


def _short_sock_path():
    """Generate a short socket path that fits macOS 104-char limit."""
    return os.path.join(tempfile.gettempdir(), f"t_{uuid.uuid4().hex[:8]}.sock")


def test_server_receives_message():
    sock_path = _short_sock_path()
    callback = MagicMock()
    server = SocketServer(sock_path, callback)
    try:
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
    finally:
        server.stop()


def test_server_handles_malformed_json():
    sock_path = _short_sock_path()
    callback = MagicMock()
    server = SocketServer(sock_path, callback)
    try:
        server.start()
        time.sleep(0.1)

        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(sock_path)
        client.sendall(b"not json{{{")
        client.close()
        time.sleep(0.2)

        # Should not crash, callback not called for bad data
        callback.assert_not_called()
    finally:
        server.stop()


def test_server_multiple_messages():
    sock_path = _short_sock_path()
    callback = MagicMock()
    server = SocketServer(sock_path, callback)
    try:
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
    finally:
        server.stop()

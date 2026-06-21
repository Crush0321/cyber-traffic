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

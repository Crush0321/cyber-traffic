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

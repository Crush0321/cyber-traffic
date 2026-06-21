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

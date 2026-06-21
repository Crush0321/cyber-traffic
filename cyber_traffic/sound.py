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

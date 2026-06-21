"""App-wide constants."""
import os

# Application name shown in menu bar
APP_NAME = "Cyber Traffic"

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

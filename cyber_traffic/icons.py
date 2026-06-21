"""Menu bar icon rendering with color support via rumps/PyObjC."""
import rumps
from cyber_traffic.config import COLORS, ICONS


def _make_colored_icon(char: str, rgb: tuple) -> rumps.MenuItem:
    """Create an attributed title string for menu bar display."""
    # rumps supports NSAttributedTitle via PyObjC
    from AppKit import NSColor, NSFont, NSAttributedString, NSMutableAttributedString
    r, g, b = rgb
    color = NSColor.colorWithCalibratedRed_green_blue_alpha_(r / 255, g / 255, b / 255, 1.0)
    font = NSFont.systemFontOfSize_(14.0)
    attrs = {
        "NSColor": color,
        "NSFont": font,
    }
    return NSAttributedString.alloc().initWithString_attributes_(char, attrs)


# Pre-render all icons at import time
ICONS_RENDERED = {}
for _state in ("IDLE", "WORKING", "CONFIRM", "ERROR"):
    ICONS_RENDERED[_state] = _make_colored_icon(ICONS[_state], COLORS[_state])


def get_icon(state: str):
    """Return the rendered icon for a given state."""
    return ICONS_RENDERED.get(state, ICONS_RENDERED["IDLE"])

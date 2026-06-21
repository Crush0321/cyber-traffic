"""Auto-configure Claude Code hooks in ~/.claude/settings.json."""
import json
import os
import sys


def get_hook_command() -> str:
    """Get the absolute path to the hook script."""
    # Resolve relative to the package root
    pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hook_path = os.path.join(pkg_dir, "hooks", "notify_traffic.py")
    return f"python3 {hook_path}"


def setup():
    """Add Cyber Traffic hooks to ~/.claude/settings.json."""
    settings_path = os.path.expanduser("~/.claude/settings.json")

    # Read existing settings
    settings = {}
    if os.path.exists(settings_path):
        with open(settings_path, "r") as f:
            settings = json.load(f)

    # Ensure hooks key exists
    if "hooks" not in settings:
        settings["hooks"] = {}

    hook_cmd = get_hook_command()
    hook_entry = [{"type": "command", "command": hook_cmd}]

    # Add hooks (don't duplicate)
    for hook_name in ("PreToolUse", "Stop", "Notification"):
        existing = settings["hooks"].get(hook_name, [])
        # Check if our hook is already configured
        if not any(e.get("command") == hook_cmd for e in existing):
            existing.append(hook_entry[0])
            settings["hooks"][hook_name] = existing

    # Write back
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    print(f"✅ Hooks configured in {settings_path}")
    print(f"   Hook command: {hook_cmd}")
    print(f"   Hooks: PreToolUse, Stop, Notification")
    print()
    print("Restart Claude Code to activate the hooks.")

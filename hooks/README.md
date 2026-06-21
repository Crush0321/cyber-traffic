# Hook 配置说明

## 自动配置（推荐）

```bash
cyber-traffic --setup
```

## 手动配置

编辑 `~/.claude/settings.json`，添加以下内容：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "type": "command",
        "command": "python3 /absolute/path/to/hooks/notify_traffic.py"
      }
    ],
    "Stop": [
      {
        "type": "command",
        "command": "python3 /absolute/path/to/hooks/notify_traffic.py"
      }
    ],
    "Notification": [
      {
        "type": "command",
        "command": "python3 /absolute/path/to/hooks/notify_traffic.py"
      }
    ]
  }
}
```

将 `/absolute/path/to/` 替换为实际路径。

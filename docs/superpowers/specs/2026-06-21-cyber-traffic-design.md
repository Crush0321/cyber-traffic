# Cyber Traffic — Claude Code 红绿灯状态指示器

## 概述

Cyber Traffic 是一个 macOS 菜单栏应用，通过 Claude Code 的 Hook 系统实时感知 Claude 的工作状态，用红绿灯图标直观展示。

**核心价值**：当你在等待 Claude 完成任务时，无需盯着终端，余光扫一眼菜单栏即可知道状态。

## 状态定义

| 视觉状态 | 内部状态 | 图标 | 含义 | 触发条件 |
|---------|---------|------|------|---------|
| 🟢 常亮 | `IDLE` | 绿色圆 | 空闲，等待输入 | `Stop` hook |
| 🟡 常亮 | `WORKING` | 黄色圆 | 正在思考/执行 | `PreToolUse` hook |
| 🟡 闪烁 | `CONFIRM` | 黄色圆（闪烁）| 需要你批准操作 | `PreToolUse` + 需要权限 |
| 🔴 常亮 | `ERROR` | 红色圆 | 出错或被阻塞 | `Notification` hook（错误类型）|

**状态机转换：**

```
IDLE ──PreToolUse──→ WORKING ──需要权限──→ CONFIRM
  ↑                    ↑                      │
  │                    └──────确认后───────────┘
  │
  └──Stop────────────── WORKING
  ↑
  └──5s超时──────────── ERROR ←──任意状态出错
```

**防抖规则：**
- 连续 `WORKING` 事件合并，不重复触发声音
- `CONFIRM` → `WORKING` 转换需要至少 2 秒间隔
- `ERROR` 状态保持 5 秒后自动回到 `IDLE`

## 架构

### 组件

```
┌─────────────────────────────────────────────┐
│              Claude Code CLI                │
│  hooks: PreToolUse / PostToolUse / Stop     │
│         ↓                                   │
│  hook scripts (hooks/notify_traffic.py)     │
│         ↓                                   │
│  Unix Socket → /tmp/claude-traffic.sock     │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│          菜单栏 App (rumps)                 │
│                                             │
│  Socket Server (server.py — 后台线程)        │
│         ↓                                   │
│  State Machine (state.py — 状态机+防抖)     │
│         ↓                                   │
│  Menu Bar Icon (app.py — 动态更新)           │
│  + Sound Player (sound.py — 状态变化音效)   │
│  + History Log (下拉菜单 — 状态时间线)       │
└─────────────────────────────────────────────┘
```

### 数据流

1. Claude Code 触发 hook 事件，将事件 JSON 通过 stdin 传给 hook 脚本
2. Hook 脚本解析事件类型，映射为状态，通过 Unix socket 发送给菜单栏 app
3. App 的 socket server 线程接收消息，交给状态机处理
4. 状态机判断是否需要转换状态（防抖），如果状态变化：
   - 更新菜单栏图标
   - 播放对应音效
   - 记录到历史日志

## Hook 系统

### 事件映射

| Hook 事件 | 条件 | 发送状态 | detail 示例 |
|-----------|------|---------|------------|
| `PreToolUse` | 不需要权限 | `WORKING` | `"执行: Read"` |
| `PreToolUse` | 需要权限确认 | `CONFIRM` | `"需要确认: Write"` |
| `PostToolUse` | — | `WORKING` | `"完成: Read"` |
| `Stop` | — | `IDLE` | `"完成"` |
| `Notification` | 含错误关键词 | `ERROR` | `"错误: ..."` |
| `Notification` | 其他 | `WORKING` | `"通知: ..."` |

### Socket 消息格式

```json
{
  "state": "WORKING",
  "detail": "Reading file: src/main.py",
  "timestamp": 1718976000
}
```

### 权限检测

Claude Code 的 `PreToolUse` hook 在需要用户批准时，事件中会包含 `permission_required` 相关字段。Hook 脚本通过检查事件内容判断是否需要确认。

## 音效系统

使用 macOS 系统自带音效（`/System/Library/Sounds/`），零外部依赖。

| 状态转换 | 音效文件 | 说明 |
|---------|---------|------|
| `→ WORKING` | 无 | 太频繁，不播放 |
| `→ CONFIRM` | Glass.aiff | 叮——需要你注意 |
| `CONFIRM →` | Tink.aiff | 轻响——已确认 |
| `→ ERROR` | Basso.aiff | 低沉——出错了 |
| `→ IDLE` | Hero.aiff | 完成提示 |

可通过下拉菜单一键静音。使用 `afplay` 命令播放，无需额外依赖。

## 菜单栏 UI

### 图标

菜单栏显示一个彩色圆形字符：
- 🟢 `●` 绿色 (#34C759)
- 🟡 `●` 黄色 (#FFCC00)
- 🔴 `●` 红色 (#FF3B30)

闪烁效果：0.5 秒间隔切换亮/暗版本图标。

### 下拉菜单

```
┌──────────────────────────────────────┐
│ 🟢 当前状态：空闲                    │
│    Claude Code 等待输入中             │
├──────────────────────────────────────┤
│ 状态历史                             │
│ 🟢 空闲                    14:32:05  │
│ 🟡 工作中 — 读取文件        14:31:48  │
│ 🟡 等待确认 — 写入 config   14:31:30  │
│ 🟡 工作中 — 编辑代码        14:30:15  │
│ 🟢 空闲                    14:29:50  │
├──────────────────────────────────────┤
│ ⚙️ 设置...                           │
│ 🔇 静音                              │
│ ─────────────────────                │
│ 🚪 退出                              │
└──────────────────────────────────────┘
```

## 项目结构

```
cyber-traffic/
├── README.md
├── requirements.txt          # rumps
├── setup.py                  # pip install -e .
├── cyber_traffic/
│   ├── __init__.py
│   ├── app.py               # 主入口，rumps.App 菜单栏
│   ├── server.py            # Unix Socket 后台线程
│   ├── state.py             # 状态机 + 防抖逻辑
│   ├── sound.py             # 音效播放
│   ├── icons.py             # 菜单栏图标资源
│   └── config.py            # 配置管理（socket 路径等）
├── hooks/
│   ├── notify_traffic.py    # Hook 脚本，被 Claude Code 调用
│   └── README.md            # Hook 配置说明
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-06-21-cyber-traffic-design.md
```

## 安装与使用

### 安装

```bash
cd cyber-traffic
pip install -e .
```

### 启动

```bash
cyber-traffic          # 启动菜单栏 app
```

### 配置 Hook

```bash
cyber-traffic --setup  # 自动配置 Claude Code hooks
```

`--setup` 命令读取 `~/.claude/settings.json`，追加 hook 配置：

```json
{
  "hooks": {
    "PreToolUse": [{
      "type": "command",
      "command": "python3 /path/to/hooks/notify_traffic.py"
    }],
    "Stop": [{
      "type": "command",
      "command": "python3 /path/to/hooks/notify_traffic.py"
    }],
    "Notification": [{
      "type": "command",
      "command": "python3 /path/to/hooks/notify_traffic.py"
    }]
  }
}
```

## 技术选型

| 决策 | 选择 | 理由 |
|-----|------|------|
| 语言 | Python | 开发快，生态好 |
| 菜单栏框架 | rumps | 最简 macOS 菜单栏库 |
| 通信方式 | Unix Socket | 实时、零延迟、无端口占用 |
| 音效 | macOS 系统音效 + afplay | 零依赖 |
| 打包 | setuptools | 标准 Python 打包 |

## 未来扩展（不在本次范围内）

- 物理红绿灯硬件（USB GPIO 控制）
- Web 仪表盘界面
- 多实例监控
- 自定义状态规则
- 菜单栏显示当前任务摘要文字

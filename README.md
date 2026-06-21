# 🚦 Cyber Traffic

Claude Code 红绿灯状态指示器 — macOS 菜单栏版本。

## 效果

菜单栏显示彩色圆点，实时反映 Claude Code 的状态：

| 图标 | 状态 | 含义 |
|------|------|------|
| 🟢 | 空闲 | Claude 等待输入 |
| 🟡 | 工作中 | Claude 正在思考/执行 |
| 🟡 闪烁 | 等待确认 | 需要你批准操作 |
| 🔴 | 错误 | 出错或被阻塞 |

## 安装

```bash
pip install -e .
```

## 使用

```bash
# 启动菜单栏 app
cyber-traffic

# 自动配置 Claude Code hooks
cyber-traffic --setup
```

`--setup` 会自动修改 `~/.claude/settings.json`，添加 hook 配置。配置完成后重启 Claude Code 即可生效。

## 功能

- ✅ 实时状态指示（绿/黄/红）
- ✅ 闪烁黄灯 = 等待确认
- ✅ 状态变化音效（可静音）
- ✅ 状态历史时间线
- ✅ 错误状态自动恢复（5秒）
- ✅ 一键配置 Claude Code hooks

## 卸载 Hook

编辑 `~/.claude/settings.json`，删除 `hooks` 中包含 `notify_traffic` 的条目。

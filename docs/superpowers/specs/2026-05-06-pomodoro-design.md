# 桌面番茄钟 设计文档

**日期：** 2026-05-06  
**技术栈：** Python + CustomTkinter  
**平台：** macOS  

---

## 需求概要

标准版番茄钟桌面应用，功能包括：
- 倒计时 + 开始/暂停/重置
- 自动切换工作/休息轮次（25/5/15 分钟）
- 桌面通知 + 提示音（osascript）
- 今日完成番茄数统计
- 普通模式与迷你悬浮模式切换
- 跟随 macOS 系统深浅色主题

---

## 文件结构

```
pomodoro/
├── main.py              # 入口，启动应用
├── app.py               # App 主类，管理窗口切换（普通/迷你）
├── timer.py             # 纯逻辑层：倒计时状态机，不依赖 UI
├── ui/
│   ├── normal_window.py # 普通模式窗口（大窗）
│   └── mini_window.py   # 迷你模式窗口（悬浮小窗）
├── notifier.py          # 桌面通知 + 提示音（封装 osascript / afplay）
└── session.py           # 今日番茄数的读写（本地 JSON 文件）
```

---

## 架构与数据流

```
timer.py（状态机）
    ↓ 回调（时间更新、阶段切换）
app.py（协调层）
    ↓ 驱动          ↓ 触发
normal/mini_window  notifier + session
```

`timer.py` 只管时间逻辑，完全不耦合 UI。UI 层通过注册回调获得更新。普通窗口和迷你窗口共享同一个计时器实例，切换模式时计时不中断。

---

## 计时器状态机

**状态流转：**

```
IDLE → WORK → SHORT_BREAK → WORK → SHORT_BREAK → WORK → SHORT_BREAK → WORK → LONG_BREAK → IDLE
每完成 4 个 WORK 阶段后，下一次休息改为 LONG_BREAK
```

**各阶段时长：**

| 状态 | 默认时长 | 说明 |
|------|---------|------|
| `IDLE` | — | 初始/重置状态，等待开始 |
| `WORK` | 25 分钟 | 专注工作阶段 |
| `SHORT_BREAK` | 5 分钟 | 短休息 |
| `LONG_BREAK` | 15 分钟 | 每完成 4 个番茄后触发 |

**核心接口（`timer.py`）：**

- `start()` — 开始或恢复计时
- `pause()` — 暂停计时
- `reset()` — 重置到 IDLE 状态
- `on_tick(callback)` — 注册每秒回调，传入剩余秒数
- `on_phase_change(callback)` — 注册阶段切换回调，传入新阶段名

内部用 `after()` 驱动，不新开线程，避免线程安全问题。

---

## UI 布局

### 普通模式窗口

```
┌─────────────────────────────┐
│  🍅 番茄钟          [迷你] │
├─────────────────────────────┤
│                             │
│   ● 工作中  (第 2 / 4 个)  │
│                             │
│        24:35               │
│     （大号倒计时数字）      │
│                             │
│   [  开始  ]  [  重置  ]   │
│                             │
│   今日完成：███░░  3 个    │
└─────────────────────────────┘
```

### 迷你模式窗口

```
┌──────────────────┐
│ 🍅 24:35  ⏸ [□] │
└──────────────────┘
```

- 始终置顶，可拖动
- 显示阶段图标（🍅 工作 / ☕ 休息）和剩余时间
- ⏸/▶ 切换暂停/继续
- `[□]` 展开为普通模式

**主题：** CustomTkinter 自动检测系统深浅色，`appearance_mode="System"`。

---

## 通知与提示音

使用 `osascript` 发送 macOS 原生通知（同时包含声音）：

```bash
osascript -e 'display notification "休息一下！" with title "番茄钟" sound name "Glass"'
```

备选：若 osascript 不可用，回退到 `afplay /System/Library/Sounds/Glass.aiff`。

**触发时机：**

| 触发条件 | 通知文案 |
|---------|---------|
| WORK 结束 | "专注结束，该休息了！" |
| SHORT_BREAK 结束 | "休息结束，继续加油！" |
| LONG_BREAK 结束 | "长休息结束，开始新一轮！" |

---

## 今日番茄数持久化

存储路径：`~/.pomodoro/session.json`

格式：
```json
{"date": "2026-05-06", "count": 3}
```

- 每次 WORK 阶段完成时 count +1
- 应用启动时检查日期，若与今日不符则自动归零

---

## 依赖

```
customtkinter>=5.2.0
```

Python 标准库（无需额外安装）：`json`, `os`, `subprocess`, `datetime`

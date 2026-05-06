# 桌面番茄钟 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用 Python + CustomTkinter 构建一个 macOS 桌面番茄钟，支持自动工作/休息轮次切换、桌面通知、今日番茄数统计和普通/迷你双窗口模式。

**Architecture:** 计时器逻辑（`timer.py`）与 UI 完全解耦，通过回调传递状态更新；`app.py` 作为协调层管理两个窗口实例和模式切换；通知与持久化各自独立模块。

**Tech Stack:** Python 3.10+, customtkinter>=5.2.0, macOS osascript/afplay

---

## 文件结构

```
pomodoro/
├── main.py              # 入口
├── app.py               # 协调层，管理窗口切换
├── timer.py             # 纯逻辑：状态机 + 倒计时
├── session.py           # 今日番茄数读写（~/.pomodoro/session.json）
├── notifier.py          # macOS 通知 + 提示音
└── ui/
    ├── __init__.py
    ├── normal_window.py # 普通模式大窗
    └── mini_window.py   # 迷你悬浮小窗
tests/
├── test_timer.py
└── test_session.py
requirements.txt
```

---

### Task 1: 项目脚手架

**Files:**
- Create: `pomodoro/` 目录结构
- Create: `requirements.txt`
- Create: `tests/` 目录

- [ ] **Step 1: 创建目录结构**

```bash
cd /Users/zhangdingan/MyProject/frist-cc
mkdir -p pomodoro/ui tests
touch pomodoro/__init__.py pomodoro/ui/__init__.py
```

- [ ] **Step 2: 创建 requirements.txt**

```
customtkinter>=5.2.0
pytest>=7.0
```

- [ ] **Step 3: 创建并激活虚拟环境，安装依赖**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Expected: `Successfully installed customtkinter-...`

- [ ] **Step 4: 验证安装**

```bash
python3 -c "import customtkinter; print(customtkinter.__version__)"
```

Expected: 打印版本号，无报错。

- [ ] **Step 5: Commit**

```bash
git add requirements.txt pomodoro/__init__.py pomodoro/ui/__init__.py
git commit -m "chore: project scaffold with customtkinter dependency"
```

---

### Task 2: timer.py — 计时器状态机（TDD）

**Files:**
- Create: `pomodoro/timer.py`
- Create: `tests/test_timer.py`

- [ ] **Step 1: 写失败测试——初始状态**

`tests/test_timer.py`:

```python
import pytest
from pomodoro.timer import PomodoroTimer, Phase

def test_initial_state():
    t = PomodoroTimer()
    assert t.phase == Phase.IDLE
    assert t.remaining == 25 * 60
    assert not t.running

def test_work_duration():
    t = PomodoroTimer()
    assert t.durations[Phase.WORK] == 25 * 60

def test_short_break_duration():
    t = PomodoroTimer()
    assert t.durations[Phase.SHORT_BREAK] == 5 * 60

def test_long_break_duration():
    t = PomodoroTimer()
    assert t.durations[Phase.LONG_BREAK] == 15 * 60
```

- [ ] **Step 2: 运行确认测试失败**

```bash
source .venv/bin/activate
pytest tests/test_timer.py -v
```

Expected: FAILED（ModuleNotFoundError: pomodoro.timer）

- [ ] **Step 3: 实现 timer.py 基础结构**

`pomodoro/timer.py`:

```python
from enum import Enum, auto


class Phase(Enum):
    IDLE = auto()
    WORK = auto()
    SHORT_BREAK = auto()
    LONG_BREAK = auto()


class PomodoroTimer:
    def __init__(self):
        self.durations = {
            Phase.WORK: 25 * 60,
            Phase.SHORT_BREAK: 5 * 60,
            Phase.LONG_BREAK: 15 * 60,
        }
        self.phase = Phase.IDLE
        self.remaining = self.durations[Phase.WORK]
        self.running = False
        self._completed_work = 0
        self._tick_callback = None    # 单槽，切换窗口时覆盖，避免回调残留
        self._phase_callback = None
        self._tk = None

    def on_tick(self, callback):
        self._tick_callback = callback

    def on_phase_change(self, callback):
        self._phase_callback = callback
```

- [ ] **Step 4: 运行确认基础测试通过**

```bash
pytest tests/test_timer.py -v
```

Expected: 4 PASSED

- [ ] **Step 5: 写失败测试——start/pause/reset**

在 `tests/test_timer.py` 末尾追加：

```python
def test_start_sets_running():
    t = PomodoroTimer()
    t.start()
    assert t.running
    assert t.phase == Phase.WORK

def test_pause_stops_running():
    t = PomodoroTimer()
    t.start()
    t.pause()
    assert not t.running

def test_reset_returns_to_idle():
    t = PomodoroTimer()
    t.start()
    t.reset()
    assert t.phase == Phase.IDLE
    assert not t.running
    assert t.remaining == t.durations[Phase.WORK]
    assert t._completed_work == 0
```

- [ ] **Step 6: 运行确认新测试失败**

```bash
pytest tests/test_timer.py -v
```

Expected: 3 FAILED（AttributeError: 'PomodoroTimer' object has no attribute 'start'）

- [ ] **Step 7: 实现 start/pause/reset**

在 `PomodoroTimer` 类中追加：

```python
    def start(self, tk_widget=None):
        if tk_widget is not None:
            self._tk = tk_widget
        if self.phase == Phase.IDLE:
            self.phase = Phase.WORK
            self.remaining = self.durations[Phase.WORK]
            if self._phase_callback:
                self._phase_callback(self.phase, self._completed_work)
        self.running = True
        if self._tk is not None:
            self._schedule_tick()

    def pause(self):
        self.running = False

    def reset(self):
        self.running = False
        self.phase = Phase.IDLE
        self.remaining = self.durations[Phase.WORK]
        self._completed_work = 0
        if self._phase_callback:
            self._phase_callback(self.phase, self._completed_work)
```

- [ ] **Step 8: 运行确认 start/pause/reset 测试通过**

```bash
pytest tests/test_timer.py -v
```

Expected: 7 PASSED

- [ ] **Step 9: 写失败测试——阶段自动切换逻辑**

在 `tests/test_timer.py` 末尾追加：

```python
def test_next_phase_after_work_is_short_break():
    t = PomodoroTimer()
    t.start()
    t._completed_work = 0
    next_phase = t._compute_next_phase()
    assert next_phase == Phase.SHORT_BREAK

def test_next_phase_after_4_work_is_long_break():
    t = PomodoroTimer()
    t.start()
    t._completed_work = 3  # 即将完成第4个
    next_phase = t._compute_next_phase()
    assert next_phase == Phase.LONG_BREAK

def test_next_phase_after_break_is_work():
    t = PomodoroTimer()
    t.phase = Phase.SHORT_BREAK
    next_phase = t._compute_next_phase()
    assert next_phase == Phase.WORK
```

- [ ] **Step 10: 运行确认测试失败**

```bash
pytest tests/test_timer.py -v
```

Expected: 3 FAILED

- [ ] **Step 11: 实现 _compute_next_phase 和 _tick**

在 `PomodoroTimer` 类中追加：

```python
    def _compute_next_phase(self):
        if self.phase in (Phase.SHORT_BREAK, Phase.LONG_BREAK):
            return Phase.WORK
        # 当前是 WORK，判断是否触发长休息
        if (self._completed_work + 1) % 4 == 0:
            return Phase.LONG_BREAK
        return Phase.SHORT_BREAK

    def _advance_phase(self):
        if self.phase == Phase.WORK:
            self._completed_work += 1
        next_phase = self._compute_next_phase()
        self.phase = next_phase
        self.remaining = self.durations.get(next_phase, self.durations[Phase.WORK])
        if self._phase_callback:
            self._phase_callback(self.phase, self._completed_work)

    def _schedule_tick(self):
        if not self.running or self._tk is None:
            return
        self._tk.after(1000, self._tick)

    def _tick(self):
        if not self.running:
            return
        self.remaining -= 1
        if self._tick_callback:
            self._tick_callback(self.remaining)
        if self.remaining <= 0:
            self._advance_phase()
            if self.phase != Phase.IDLE:
                self._schedule_tick()
            return
        self._schedule_tick()
```

- [ ] **Step 12: 运行全部测试**

```bash
pytest tests/test_timer.py -v
```

Expected: 10 PASSED

- [ ] **Step 13: Commit**

```bash
git add pomodoro/timer.py tests/test_timer.py
git commit -m "feat: timer state machine with phase auto-switching"
```

---

### Task 3: session.py — 今日番茄数持久化（TDD）

**Files:**
- Create: `pomodoro/session.py`
- Create: `tests/test_session.py`

- [ ] **Step 1: 写失败测试**

`tests/test_session.py`:

```python
import pytest
import json
import tempfile
import os
from datetime import date
from unittest.mock import patch
from pomodoro.session import Session


def make_session(tmp_path):
    return Session(data_dir=str(tmp_path))


def test_initial_count_is_zero(tmp_path):
    s = make_session(tmp_path)
    assert s.count == 0


def test_increment_increases_count(tmp_path):
    s = make_session(tmp_path)
    s.increment()
    assert s.count == 1


def test_count_persists_across_instances(tmp_path):
    s1 = make_session(tmp_path)
    s1.increment()
    s1.increment()
    s2 = make_session(tmp_path)
    assert s2.count == 2


def test_count_resets_on_new_day(tmp_path):
    s1 = make_session(tmp_path)
    s1.increment()
    # 模拟昨天的数据
    session_file = tmp_path / "session.json"
    data = json.loads(session_file.read_text())
    data["date"] = "2000-01-01"
    session_file.write_text(json.dumps(data))

    s2 = make_session(tmp_path)
    assert s2.count == 0
```

- [ ] **Step 2: 运行确认测试失败**

```bash
pytest tests/test_session.py -v
```

Expected: FAILED（ModuleNotFoundError）

- [ ] **Step 3: 实现 session.py**

`pomodoro/session.py`:

```python
import json
import os
from datetime import date
from pathlib import Path


class Session:
    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = os.path.expanduser("~/.pomodoro")
        self._path = Path(data_dir) / "session.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _load(self):
        today = str(date.today())
        if self._path.exists():
            data = json.loads(self._path.read_text())
            if data.get("date") == today:
                return data
        return {"date": today, "count": 0}

    def _save(self):
        self._path.write_text(json.dumps(self._data))

    @property
    def count(self):
        return self._data["count"]

    def increment(self):
        self._data["count"] += 1
        self._save()
```

- [ ] **Step 4: 运行全部测试**

```bash
pytest tests/test_session.py tests/test_timer.py -v
```

Expected: 全部 PASSED

- [ ] **Step 5: Commit**

```bash
git add pomodoro/session.py tests/test_session.py
git commit -m "feat: session persistence for daily pomodoro count"
```

---

### Task 4: notifier.py — 桌面通知与提示音

**Files:**
- Create: `pomodoro/notifier.py`

（notifier 依赖 osascript，不做自动化测试，用手动验证。）

- [ ] **Step 1: 实现 notifier.py**

`pomodoro/notifier.py`:

```python
import subprocess
from pomodoro.timer import Phase

_MESSAGES = {
    Phase.SHORT_BREAK: ("番茄钟", "专注结束，该休息了！"),
    Phase.LONG_BREAK:  ("番茄钟", "专注结束，好好休息一下！"),
    Phase.WORK:        ("番茄钟", "休息结束，继续加油！"),
    Phase.IDLE:        ("番茄钟", "长休息结束，开始新一轮！"),
}


def notify(phase: Phase):
    title, message = _MESSAGES.get(phase, ("番茄钟", ""))
    if not message:
        return
    script = (
        f'display notification "{message}" with title "{title}" sound name "Glass"'
    )
    try:
        subprocess.run(["osascript", "-e", script], check=True, timeout=5)
    except Exception:
        _fallback_sound()


def _fallback_sound():
    try:
        subprocess.run(
            ["afplay", "/System/Library/Sounds/Glass.aiff"],
            check=True,
            timeout=5,
        )
    except Exception:
        pass
```

- [ ] **Step 2: 手动验证通知**

```bash
source .venv/bin/activate
python3 -c "
from pomodoro.timer import Phase
from pomodoro.notifier import notify
notify(Phase.SHORT_BREAK)
"
```

Expected: macOS 右上角弹出通知，并播放 Glass 音效。

- [ ] **Step 3: Commit**

```bash
git add pomodoro/notifier.py
git commit -m "feat: macOS desktop notifier with sound"
```

---

### Task 5: ui/normal_window.py — 普通模式窗口

**Files:**
- Create: `pomodoro/ui/normal_window.py`

- [ ] **Step 1: 实现 normal_window.py**

`pomodoro/ui/normal_window.py`:

```python
import customtkinter as ctk
from pomodoro.timer import Phase


class NormalWindow(ctk.CTkToplevel):
    def __init__(self, app, timer, session):
        super().__init__()
        self._app = app
        self._timer = timer
        self._session = session

        self.title("番茄钟")
        self.resizable(False, False)
        self.geometry("300x320")
        self.protocol("WM_DELETE_WINDOW", self.destroy)

        self._build_ui()
        self._timer.on_tick(self._on_tick)
        self._timer.on_phase_change(self._on_phase_change)
        self._refresh_display()

    def _build_ui(self):
        # 顶栏
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 0))
        ctk.CTkLabel(top, text="🍅 番茄钟", font=("", 14, "bold")).pack(side="left")
        ctk.CTkButton(
            top, text="迷你", width=56, height=26,
            command=self._switch_to_mini,
        ).pack(side="right")

        # 阶段标签
        self._phase_label = ctk.CTkLabel(self, text="", font=("", 13))
        self._phase_label.pack(pady=(16, 0))

        # 倒计时
        self._time_label = ctk.CTkLabel(self, text="25:00", font=("", 56, "bold"))
        self._time_label.pack(pady=(4, 0))

        # 按钮行
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=16)
        self._start_btn = ctk.CTkButton(
            btn_row, text="开始", width=100, command=self._toggle_start
        )
        self._start_btn.pack(side="left", padx=8)
        ctk.CTkButton(
            btn_row, text="重置", width=100, command=self._reset
        ).pack(side="left", padx=8)

        # 今日番茄数
        self._count_label = ctk.CTkLabel(self, text="", font=("", 12))
        self._count_label.pack(pady=(0, 12))

    def _refresh_display(self):
        self._update_time(self._timer.remaining)
        self._update_phase(self._timer.phase, self._timer._completed_work)
        self._update_count()
        self._start_btn.configure(
            text="暂停" if self._timer.running else "开始"
        )

    def _update_time(self, remaining):
        m, s = divmod(remaining, 60)
        self._time_label.configure(text=f"{m:02d}:{s:02d}")

    def _update_phase(self, phase, completed):
        icons = {
            Phase.IDLE: "等待开始",
            Phase.WORK: f"🍅 工作中（第 {completed % 4 + 1} / 4 个）",
            Phase.SHORT_BREAK: "☕ 短休息",
            Phase.LONG_BREAK: "🛋️ 长休息",
        }
        self._phase_label.configure(text=icons.get(phase, ""))

    def _update_count(self):
        count = self._session.count
        filled = min(count, 8)
        bar = "🍅" * filled + "○" * (8 - filled)
        self._count_label.configure(text=f"今日完成：{bar}  {count} 个")

    def _on_tick(self, remaining):
        self._update_time(remaining)

    def _on_phase_change(self, phase, completed):
        self._update_phase(phase, completed)
        self._update_count()
        self._start_btn.configure(
            text="暂停" if self._timer.running else "开始"
        )
        from pomodoro.notifier import notify
        notify(phase)
        # WORK 结束进入休息时计数（不是进入 WORK 时）
        if phase in (Phase.SHORT_BREAK, Phase.LONG_BREAK):
            self._session.increment()

    def _toggle_start(self):
        if self._timer.running:
            self._timer.pause()
            self._start_btn.configure(text="开始")
        else:
            self._timer.start(tk_widget=self)
            self._start_btn.configure(text="暂停")

    def _reset(self):
        self._timer.reset()
        self._refresh_display()

    def _switch_to_mini(self):
        self._app.switch_to_mini()
```

- [ ] **Step 2: Commit**

```bash
git add pomodoro/ui/normal_window.py
git commit -m "feat: normal window UI with phase display and controls"
```

---

### Task 6: ui/mini_window.py — 迷你悬浮窗口

**Files:**
- Create: `pomodoro/ui/mini_window.py`

- [ ] **Step 1: 实现 mini_window.py**

`pomodoro/ui/mini_window.py`:

```python
import customtkinter as ctk
from pomodoro.timer import Phase


class MiniWindow(ctk.CTkToplevel):
    def __init__(self, app, timer, session):
        super().__init__()
        self._app = app
        self._timer = timer
        self._session = session

        self.overrideredirect(True)   # 去掉标题栏
        self.attributes("-topmost", True)
        self.geometry("200x44+100+100")

        self._build_ui()
        self._timer.on_tick(self._on_tick)
        self._timer.on_phase_change(self._on_phase_change)
        self._refresh()

        # 拖拽支持
        self.bind("<ButtonPress-1>", self._drag_start)
        self.bind("<B1-Motion>", self._drag_motion)

    def _build_ui(self):
        frame = ctk.CTkFrame(self, corner_radius=10)
        frame.pack(fill="both", expand=True)

        self._icon_label = ctk.CTkLabel(frame, text="🍅", font=("", 14))
        self._icon_label.pack(side="left", padx=(8, 0))

        self._time_label = ctk.CTkLabel(frame, text="25:00", font=("", 15, "bold"))
        self._time_label.pack(side="left", padx=6)

        self._play_btn = ctk.CTkButton(
            frame, text="▶", width=28, height=28,
            command=self._toggle_start,
        )
        self._play_btn.pack(side="left", padx=2)

        ctk.CTkButton(
            frame, text="□", width=28, height=28,
            command=self._expand,
        ).pack(side="left", padx=(2, 6))

    def _refresh(self):
        self._update_time(self._timer.remaining)
        self._update_icon(self._timer.phase)
        self._play_btn.configure(text="⏸" if self._timer.running else "▶")

    def _update_time(self, remaining):
        m, s = divmod(remaining, 60)
        self._time_label.configure(text=f"{m:02d}:{s:02d}")

    def _update_icon(self, phase):
        icons = {Phase.WORK: "🍅", Phase.SHORT_BREAK: "☕", Phase.LONG_BREAK: "🛋️", Phase.IDLE: "🍅"}
        self._icon_label.configure(text=icons.get(phase, "🍅"))

    def _on_tick(self, remaining):
        self._update_time(remaining)

    def _on_phase_change(self, phase, completed):
        self._update_icon(phase)
        self._play_btn.configure(text="⏸" if self._timer.running else "▶")
        from pomodoro.notifier import notify
        notify(phase)
        # WORK 结束进入休息时计数（不是进入 WORK 时）
        if phase in (Phase.SHORT_BREAK, Phase.LONG_BREAK):
            self._session.increment()

    def _toggle_start(self):
        if self._timer.running:
            self._timer.pause()
            self._play_btn.configure(text="▶")
        else:
            self._timer.start(tk_widget=self)
            self._play_btn.configure(text="⏸")

    def _expand(self):
        self._app.switch_to_normal()

    def _drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_motion(self, event):
        x = self.winfo_x() + event.x - self._drag_x
        y = self.winfo_y() + event.y - self._drag_y
        self.geometry(f"+{x}+{y}")

    def destroy(self):
        super().destroy()

    def show(self):
        self.deiconify()
```

- [ ] **Step 2: Commit**

```bash
git add pomodoro/ui/mini_window.py
git commit -m "feat: mini floating window with drag support and always-on-top"
```

---

### Task 7: app.py — 协调层与窗口切换

**Files:**
- Create: `pomodoro/app.py`

- [ ] **Step 1: 实现 app.py**

`pomodoro/app.py`:

```python
import customtkinter as ctk
from pomodoro.timer import PomodoroTimer
from pomodoro.session import Session
from pomodoro.ui.normal_window import NormalWindow
from pomodoro.ui.mini_window import MiniWindow


class App:
    def __init__(self):
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self._root = ctk.CTk()
        self._root.withdraw()  # 隐藏根窗口，只显示 Toplevel

        self._timer = PomodoroTimer()
        self._session = Session()

        self._normal: NormalWindow | None = None
        self._mini: MiniWindow | None = None

        self.switch_to_normal()

    def switch_to_normal(self):
        if self._mini and self._mini.winfo_exists():
            self._mini.destroy()
            self._mini = None
        self._normal = NormalWindow(self, self._timer, self._session)
        self._normal.lift()

    def switch_to_mini(self):
        if self._normal and self._normal.winfo_exists():
            self._normal.destroy()
            self._normal = None
        self._mini = MiniWindow(self, self._timer, self._session)

    def run(self):
        self._root.mainloop()
```

- [ ] **Step 2: Commit**

```bash
git add pomodoro/app.py
git commit -m "feat: app coordinator for window mode switching"
```

---

### Task 8: main.py — 入口与端到端手动测试

**Files:**
- Create: `pomodoro/main.py`

- [ ] **Step 1: 实现 main.py**

`pomodoro/main.py`:

```python
from pomodoro.app import App


def main():
    app = App()
    app.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 运行全部自动化测试**

```bash
source .venv/bin/activate
pytest tests/ -v
```

Expected: 全部 PASSED

- [ ] **Step 3: 手动端到端测试——普通模式**

```bash
source .venv/bin/activate
python3 -m pomodoro.main
```

验证清单：
- [ ] 普通模式窗口正常显示，深浅色跟随系统
- [ ] 点击"开始"后倒计时开始，按钮变"暂停"
- [ ] 点击"暂停"后倒计时停止
- [ ] 点击"重置"后恢复到 25:00，阶段显示"等待开始"
- [ ] 点击"迷你"后切换为小悬浮窗，计时不中断

- [ ] **Step 4: 手动端到端测试——迷你模式**

验证清单：
- [ ] 迷你窗口始终置顶
- [ ] 可拖动到屏幕任意位置
- [ ] ▶/⏸ 按钮正常切换
- [ ] □ 按钮展开回普通模式

- [ ] **Step 5: 快速倒计时测试通知**

临时修改 `timer.py` 中 `durations` 的值为短时间来验证通知：

```python
# 临时测试——在 PomodoroTimer.__init__ 中改为：
self.durations = {
    Phase.WORK: 5,           # 5 秒
    Phase.SHORT_BREAK: 3,    # 3 秒
    Phase.LONG_BREAK: 3,
}
```

运行应用，开始计时，5 秒后验证：
- [ ] macOS 右上角出现通知
- [ ] 播放 Glass 音效
- [ ] 自动切换到短休息阶段
- [ ] 今日番茄数 +1

测试完毕后恢复原始时长（25/5/15 分钟）。

- [ ] **Step 6: 最终 Commit**

```bash
git add pomodoro/main.py
git commit -m "feat: entry point — pomodoro app complete"
```

---

## 完成标准

- [ ] `pytest tests/ -v` 全绿
- [ ] 普通/迷你双模式正常切换，计时不中断
- [ ] 计时结束时 macOS 通知 + 声音正常触发
- [ ] 今日番茄数准确统计并显示
- [ ] 界面跟随系统深浅色主题

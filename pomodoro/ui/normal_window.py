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

import customtkinter as ctk
from pomodoro.timer import Phase
from pomodoro.notifier import notify as _notify


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
        self._timer.on_tick(self._on_tick, tk_widget=self)
        self._timer.on_phase_change(self._on_phase_change)
        self._refresh()

        # 拖拽只绑定在非交互区域，避免影响按钮点击
        for widget in (self._icon_label, self._time_label):
            widget.bind("<ButtonPress-1>", self._drag_start)
            widget.bind("<B1-Motion>", self._drag_motion)

        self.after(200, self.focus_force)

    def _build_ui(self):
        self._frame = ctk.CTkFrame(self, corner_radius=10)
        self._frame.pack(fill="both", expand=True)

        self._icon_label = ctk.CTkLabel(self._frame, text="🍅", font=("", 14))
        self._icon_label.pack(side="left", padx=(8, 0))

        self._time_label = ctk.CTkLabel(self._frame, text="25:00", font=("", 15, "bold"))
        self._time_label.pack(side="left", padx=6)

        self._play_btn = ctk.CTkButton(
            self._frame, text="▶", width=28, height=28,
            command=self._toggle_start,
        )
        self._play_btn.pack(side="left", padx=2)

        ctk.CTkButton(
            self._frame, text="□", width=28, height=28,
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

    def _on_phase_change(self, phase, completed, notify=True):
        self._update_icon(phase)
        self._play_btn.configure(text="⏸" if self._timer.running else "▶")
        if notify:
            _notify(phase)
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
        self._drag_x = event.x_root
        self._drag_y = event.y_root

    def _drag_motion(self, event):
        x = self.winfo_x() + event.x_root - self._drag_x
        y = self.winfo_y() + event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")
        self._drag_x = event.x_root
        self._drag_y = event.y_root


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
        if self._normal and self._normal.winfo_exists():
            self._normal.destroy()
            self._normal = None
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

    def quit(self):
        self._root.destroy()

    def run(self):
        self._root.mainloop()

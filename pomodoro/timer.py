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
        self._after_id = None

    def on_tick(self, callback):
        self._tick_callback = callback

    def on_phase_change(self, callback):
        self._phase_callback = callback

    @property
    def completed_work(self) -> int:
        return self._completed_work

    def start(self, tk_widget=None):
        if self.running:
            return
        if tk_widget is not None:
            self._tk = tk_widget
        if self.phase == Phase.IDLE:
            self.phase = Phase.WORK
            self.remaining = self.durations[Phase.WORK]
            if self._phase_callback:
                self._phase_callback(self.phase, self._completed_work, notify=False)
        self.running = True
        if self._tk is not None:
            self._schedule_tick()

    def pause(self):
        self.running = False
        if self._after_id is not None and self._tk is not None:
            self._tk.after_cancel(self._after_id)
            self._after_id = None

    def reset(self):
        self.running = False
        if self._after_id is not None and self._tk is not None:
            self._tk.after_cancel(self._after_id)
            self._after_id = None
        self.phase = Phase.IDLE
        self.remaining = self.durations[Phase.WORK]
        self._completed_work = 0
        if self._phase_callback:
            self._phase_callback(self.phase, self._completed_work)

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
        self._after_id = self._tk.after(1000, self._tick)

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

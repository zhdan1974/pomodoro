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

import json
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

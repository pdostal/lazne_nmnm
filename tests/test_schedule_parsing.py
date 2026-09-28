import sys
from datetime import date, time
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "custom_components" / "lazne_nmnm"))

from parser import is_open, parse_schedules, select_schedule


def schedules():
    html = (ROOT / "tests" / "fixtures" / "schedule.html").read_text()
    return parse_schedules(html)


def test_regular_schedule() -> None:
    regular = select_schedule(schedules(), date(2026, 9, 29))
    assert regular.start == date(2026, 9, 14)
    assert regular.end is None
    tuesday = regular.days[1]
    assert is_open(tuesday.pool, time(6, 0))
    assert not is_open(tuesday.pool, time(20, 45))
    assert tuesday.wellness[0].sauna_type == "pánská"
    assert tuesday.wellness[1].sauna_type == "společná"


def test_summer_schedule_wins() -> None:
    summer = select_schedule(schedules(), date(2027, 7, 1))
    assert summer.start == date(2027, 6, 14)
    assert summer.end == date(2027, 9, 5)
    assert summer.days[0].wellness[0].start == time(17, 0)
    assert summer.days[0].wellness[0].sauna_type == "společná"


def test_unknown_date_fails() -> None:
    try:
        select_schedule(schedules(), date(2025, 1, 1))
    except ValueError as error:
        assert "no schedule covers" in str(error)
    else:
        raise AssertionError("date outside all schedules was accepted")


if __name__ == "__main__":
    test_regular_schedule()
    test_summer_schedule_wins()
    test_unknown_date_fails()
    print("schedule parser: OK")

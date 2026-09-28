import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "custom_components" / "lazne_nmnm"))

from parser import parse_occupancy


def test_occupancy() -> None:
    html = (ROOT / "tests" / "fixtures" / "occupancy.html").read_text()
    assert parse_occupancy(html) == {
        "areal": 36,
        "bazen": 25,
        "fitness": 0,
        "wellness": 11,
        "koupele": 0,
        "masaze": 0,
        "solarium": 0,
    }


def test_missing_area_fails() -> None:
    try:
        parse_occupancy("<table><tr><td>Areál</td><td>1</td></tr></table>")
    except ValueError as error:
        assert "missing occupancy areas" in str(error)
    else:
        raise AssertionError("incomplete occupancy table was accepted")


if __name__ == "__main__":
    test_occupancy()
    test_missing_area_fails()
    print("occupancy parser: OK")

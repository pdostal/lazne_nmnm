"""Dependency-free parsers for the lazne.nmnm.cz HTML pages."""

import re
from dataclasses import dataclass
from datetime import date, time
from html import unescape
from html.parser import HTMLParser

AREA_LABELS = {
    "Areál": "areal",
    "Bazén": "bazen",
    "Fitness": "fitness",
    "GWellness": "wellness",
    "Wellness": "wellness",
    "Koupele": "koupele",
    "LMasáže": "masaze",
    "Masáže": "masaze",
    "Solárium": "solarium",
}
EXPECTED_AREAS = frozenset(AREA_LABELS.values())
WEEKDAYS = ("Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle")


@dataclass(frozen=True)
class TimeSlot:
    """One opening-hours interval."""

    start: time
    end: time
    sauna_type: str | None = None


@dataclass(frozen=True)
class DaySchedule:
    """Opening hours for one weekday."""

    pool: tuple[TimeSlot, ...]
    fitness: tuple[TimeSlot, ...]
    wellness: tuple[TimeSlot, ...]
    raw_pool: str
    raw_fitness: str
    raw_wellness: str


@dataclass(frozen=True)
class SeasonSchedule:
    """A dated weekly schedule."""

    name: str
    start: date
    end: date | None
    days: tuple[DaySchedule, ...]


@dataclass
class _Table:
    context: str
    rows: list[list[str]]


class _TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[_Table] = []
        self._outside: list[str] = []
        self._table: _Table | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table" and self._table is None:
            context = _clean(" ".join(self._outside))[-1000:]
            self._table = _Table(context, [])
            self._outside.clear()
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("td", "th") and self._cell is not None and self._row is not None:
            self._row.append(_clean(" ".join(self._cell)))
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            self._table.rows.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)
        elif self._table is None and data.strip():
            self._outside.append(data)


def _clean(value: str) -> str:
    return " ".join(unescape(value).replace("\xa0", " ").split())


def _tables(document: str) -> list[_Table]:
    parser = _TableParser()
    parser.feed(document)
    return parser.tables


def parse_occupancy(document: str) -> dict[str, int]:
    """Parse all expected visitor counts from an HTML table."""
    values: dict[str, int] = {}
    for table in _tables(document):
        for row in table.rows:
            if len(row) != 2 or row[0] not in AREA_LABELS or not row[1].isdigit():
                continue
            values[AREA_LABELS[row[0]]] = int(row[1])

    missing = EXPECTED_AREAS - values.keys()
    if missing:
        raise ValueError(f"missing occupancy areas: {', '.join(sorted(missing))}")
    return values


_RANGE_RE = re.compile(
    r"(?P<sh>\d{1,2}):(?P<sm>\d{2})\s*[-–—]\s*(?P<eh>\d{1,2}):(?P<em>\d{2})"
)
_DATE_RANGE_RE = re.compile(
    r"(?P<sd>\d{1,2})\s*\.\s*(?P<sm>\d{1,2})\s*\.\s*(?:(?P<sy>\d{4})\s*)?[-–—]\s*"
    r"(?P<ed>\d{1,2})\s*\.\s*(?P<em>\d{1,2})\s*\.\s*(?P<ey>\d{4})"
)
_START_DATE_RE = re.compile(
    r"\bod\s+(?P<d>\d{1,2})\s*\.\s*(?P<m>\d{1,2})\s*\.\s*(?P<y>\d{4})", re.IGNORECASE
)


def _slots(value: str, sauna: bool = False) -> tuple[TimeSlot, ...]:
    matches = list(_RANGE_RE.finditer(value))
    slots = []
    for index, match in enumerate(matches):
        suffix = value[
            match.end() : matches[index + 1].start()
            if index + 1 < len(matches)
            else None
        ].lower()
        sauna_type = None
        if sauna:
            if "pánsk" in suffix:
                sauna_type = "pánská"
            elif "dámsk" in suffix:
                sauna_type = "dámská"
            else:
                sauna_type = "společná"
        slots.append(
            TimeSlot(
                time(int(match["sh"]), int(match["sm"])),
                time(int(match["eh"]), int(match["em"])),
                sauna_type,
            )
        )
    return tuple(slots)


def _dates(context: str) -> tuple[date, date | None]:
    if match := _DATE_RANGE_RE.search(context):
        end_year = int(match["ey"])
        start_year = int(match["sy"] or end_year)
        if match["sy"] is None and int(match["sm"]) > int(match["em"]):
            start_year -= 1
        return (
            date(start_year, int(match["sm"]), int(match["sd"])),
            date(end_year, int(match["em"]), int(match["ed"])),
        )
    if match := _START_DATE_RE.search(context):
        return date(int(match["y"]), int(match["m"]), int(match["d"])), None
    raise ValueError(f"schedule date not found near table: {context[-200:]}")


def parse_schedules(document: str) -> tuple[SeasonSchedule, ...]:
    """Parse all dated pool, fitness, and wellness schedules."""
    schedules = []
    for table in _tables(document):
        if not table.rows or len(table.rows[0]) < 4:
            continue
        headers = table.rows[0]
        if not {"Bazén", "Fitness", "Wellness"}.issubset(headers):
            continue
        if len(headers) != 4 or headers[1:] != ["Bazén", "Fitness", "Wellness"]:
            raise ValueError(f"unexpected schedule columns: {', '.join(headers)}")
        if len(table.rows) != 8:
            raise ValueError(f"expected 7 schedule weekdays, got {len(table.rows) - 1}")

        days = []
        for expected_day, row in zip(WEEKDAYS, table.rows[1:], strict=True):
            if len(row) != 4 or row[0] != expected_day:
                actual = row[0] if row else "empty row"
                raise ValueError(f"expected weekday {expected_day}, got {actual}")
            pool, fitness, wellness = row[1:4]
            pool_slots = _slots(pool)
            fitness_slots = _slots(fitness)
            wellness_slots = _slots(wellness, sauna=True)
            if not pool_slots or not fitness_slots or not wellness_slots:
                raise ValueError(f"opening hours missing for {expected_day}")
            days.append(
                DaySchedule(
                    pool_slots, fitness_slots, wellness_slots, pool, fitness, wellness
                )
            )

        start, end = _dates(table.context)
        name = table.context[-200:] or f"Schedule from {start.isoformat()}"
        schedules.append(SeasonSchedule(name, start, end, tuple(days)))

    if not schedules:
        raise ValueError("no opening-hours tables found")
    return tuple(schedules)


def select_schedule(
    schedules: tuple[SeasonSchedule, ...], today: date
) -> SeasonSchedule:
    """Select a bounded season first, then the newest open-ended schedule."""
    bounded = [
        schedule
        for schedule in schedules
        if schedule.end and schedule.start <= today <= schedule.end
    ]
    if bounded:
        return max(bounded, key=lambda schedule: schedule.start)
    open_ended = [
        schedule
        for schedule in schedules
        if schedule.end is None and schedule.start <= today
    ]
    if open_ended:
        return max(open_ended, key=lambda schedule: schedule.start)
    raise ValueError(f"no schedule covers {today.isoformat()}")


def is_open(slots: tuple[TimeSlot, ...], now: time) -> bool:
    """Return whether a time falls within any slot."""
    return any(slot.start <= now < slot.end for slot in slots)

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path
from typing import Iterable, List, Optional

try:
    from dateutil import parser as date_parser  # type: ignore
except Exception:  # pragma: no cover
    date_parser = None

COURSE_CODE_RE = re.compile(r"\b([A-Z]{2,4}\s?\d{3})\b", re.IGNORECASE)
PDF_PATH_RE = re.compile(r"([A-Za-z]:\\[^\r\n\"]+?\.pdf)", re.IGNORECASE)
PDF_NAME_RE = re.compile(r"([^\\/]+\.pdf)", re.IGNORECASE)


def normalize_course_code(code: str) -> str:
    return re.sub(r"\s+", " ", code.strip().upper())


def extract_course_codes(text: str) -> List[str]:
    if not text:
        return []
    codes = [normalize_course_code(m.group(1)) for m in COURSE_CODE_RE.finditer(text)]
    return sorted(set(codes))


def extract_file_paths(text: str) -> List[str]:
    if not text:
        return []
    paths = [m.group(1) for m in PDF_PATH_RE.finditer(text)]
    names = [m.group(1) for m in PDF_NAME_RE.finditer(text)]
    for name in names:
        if name not in paths:
            paths.append(name)
    return paths


def resolve_path(candidate: str, search_dirs: Iterable[Path]) -> Optional[Path]:
    cpath = Path(candidate)
    if cpath.is_absolute() and cpath.exists():
        return cpath
    for base in search_dirs:
        test = base / candidate
        if test.exists():
            return test
    return None


def parse_date_str(text: str, today: Optional[dt.date] = None) -> Optional[dt.date]:
    if not text:
        return None
    if today is None:
        today = dt.date.today()

    t = text.lower()

    if "today" in t:
        return today
    if "tomorrow" in t:
        return today + dt.timedelta(days=1)
    if "yesterday" in t:
        return today - dt.timedelta(days=1)

    for pattern in [
        r"in\s+(\d+)\s+days?",
        r"(\d+)\s+days?\s+from\s+now",
        r"(\d+)\s+days?\s+from\s+today",
    ]:
        m = re.search(pattern, t)
        if m:
            return today + dt.timedelta(days=int(m.group(1)))

    for pattern in [
        r"(\d+)\s+days?\s+ago",
        r"(\d+)\s+days?\s+before\s+today",
    ]:
        m = re.search(pattern, t)
        if m:
            return today - dt.timedelta(days=int(m.group(1)))

    m = re.search(r"next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)", t)
    if m:
        target = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ].index(m.group(1))
        days_ahead = (target - today.weekday() + 7) % 7
        if days_ahead == 0:
            days_ahead = 7
        return today + dt.timedelta(days=days_ahead)

    if date_parser is None:
        return None

    try:
        default_dt = dt.datetime.combine(today, dt.time())
        parsed = date_parser.parse(text, fuzzy=True, default=default_dt)
    except Exception:
        return None

    parsed_date = parsed.date()
    has_year = re.search(r"\b\d{4}\b", text) is not None
    if not has_year and parsed_date < today:
        parsed_date = parsed_date.replace(year=parsed_date.year + 1)

    return parsed_date

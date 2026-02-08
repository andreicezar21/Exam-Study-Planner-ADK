import datetime as dt
from typing import Any, Dict, List

from .state import STATE

WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def build_plan() -> Dict[str, Any]:
    courses = STATE["courses"]
    prefs = STATE["preferences"]

    if not courses:
        return {"ok": False, "message": "No courses found. Ingest materials first."}

    missing_dates = [c for c in courses.values() if not c.get("exam_date")]
    if missing_dates:
        return {"ok": False, "message": "Missing exam dates for one or more courses."}

    missing_hours = [c for c in courses.values() if not c.get("estimated_hours")]
    if missing_hours:
        return {"ok": False, "message": "Missing estimated hours. Run estimation first."}

    start_date = _resolve_start_date(prefs.get("start_date"))
    last_exam = max(dt.date.fromisoformat(c["exam_date"]) for c in courses.values())
    end_date = last_exam - dt.timedelta(days=1)
    if end_date < start_date:
        end_date = start_date

    days_off = {d.strip().lower() for d in prefs.get("days_off", [])}
    daily_max = float(prefs.get("daily_max_hours", 3.0))

    remaining = {code: float(c["estimated_hours"]) for code, c in courses.items()}

    plan: List[Dict[str, Any]] = []
    for day in _date_range(start_date, end_date):
        if WEEKDAYS[day.weekday()] in days_off:
            continue

        active = [
            code
            for code, course in courses.items()
            if dt.date.fromisoformat(course["exam_date"]) > day and remaining[code] > 0
        ]
        if not active:
            continue

        targets: Dict[str, float] = {}
        total_target = 0.0
        for code in active:
            exam_date = dt.date.fromisoformat(courses[code]["exam_date"])
            days_left = _remaining_days(day, exam_date, days_off)
            target = remaining[code] / max(days_left, 1)
            targets[code] = target
            total_target += target

        scale = 1.0
        if total_target > daily_max:
            scale = daily_max / total_target

        tasks = []
        for code, target in targets.items():
            hours = round(target * scale, 2)
            if hours <= 0:
                continue
            remaining[code] = round(remaining[code] - hours, 2)
            tasks.append({"course": code, "hours": hours})

        total_hours = round(sum(t["hours"] for t in tasks), 2)
        plan.append({"date": day.isoformat(), "tasks": tasks, "total_hours": total_hours})

    STATE["study_plan"] = plan
    return {"ok": True, "days": len(plan)}


def _resolve_start_date(value: Any) -> dt.date:
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value)
        except Exception:
            pass
    return dt.date.today()


def _date_range(start: dt.date, end: dt.date) -> List[dt.date]:
    days = []
    cur = start
    while cur <= end:
        days.append(cur)
        cur += dt.timedelta(days=1)
    return days


def _remaining_days(start: dt.date, end: dt.date, days_off: set[str]) -> int:
    count = 0
    cur = start
    while cur < end:
        if WEEKDAYS[cur.weekday()] not in days_off:
            count += 1
        cur += dt.timedelta(days=1)
    return max(count, 1)

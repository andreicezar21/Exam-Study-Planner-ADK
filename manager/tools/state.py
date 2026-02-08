import copy
from typing import Any, Dict, List, Optional

from .utils import extract_course_codes, normalize_course_code, parse_date_str

DEFAULT_PREFERENCES: Dict[str, Any] = {
    "daily_max_hours": 3.0,
    "days_off": [],
    "start_date": None,
}

STATE: Dict[str, Any] = {
    "courses": {},
    "preferences": copy.deepcopy(DEFAULT_PREFERENCES),
    "study_plan": [],
}


def _ensure_course(code: str) -> Dict[str, Any]:
    code = normalize_course_code(code)
    if code not in STATE["courses"]:
        STATE["courses"][code] = {
            "code": code,
            "name": "",
            "materials": [],
            "exam_date": None,
            "estimated_hours": None,
        }
    return STATE["courses"][code]


def show_state() -> Dict[str, Any]:
    return copy.deepcopy(STATE)


def reset_state() -> Dict[str, Any]:
    STATE["courses"].clear()
    STATE["preferences"] = copy.deepcopy(DEFAULT_PREFERENCES)
    STATE["study_plan"] = []
    return show_state()


def set_preferences(
    daily_max_hours: Optional[float] = None,
    days_off: Optional[List[str]] = None,
    start_date: Optional[str] = None,
) -> Dict[str, Any]:
    prefs = STATE["preferences"]

    if daily_max_hours is not None:
        prefs["daily_max_hours"] = float(daily_max_hours)
    if days_off is not None:
        prefs["days_off"] = [d.strip().lower() for d in days_off if d.strip()]
    if start_date:
        parsed = parse_date_str(start_date)
        if parsed is None:
            return {"ok": False, "message": "Could not parse start_date."}
        prefs["start_date"] = parsed.isoformat()

    return {"ok": True, "preferences": copy.deepcopy(prefs)}


def set_exam_dates(request: str) -> Dict[str, Any]:
    date = parse_date_str(request)
    if date is None:
        return {"ok": False, "message": "Could not parse a date from that request."}

    codes = extract_course_codes(request)
    if not codes:
        codes = list(STATE["courses"].keys())
        if not codes:
            return {"ok": False, "message": "No courses found in state. Add materials first."}

    for code in codes:
        course = _ensure_course(code)
        course["exam_date"] = date.isoformat()

    return {
        "ok": True,
        "exam_date": date.isoformat(),
        "courses_updated": codes,
    }


def add_course(course_code: str, course_name: Optional[str] = None) -> Dict[str, Any]:
    if not course_code:
        return {"ok": False, "message": "course_code is required"}
    course = _ensure_course(course_code)
    if course_name:
        course["name"] = course_name
    return {"ok": True, "course": copy.deepcopy(course)}

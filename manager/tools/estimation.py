from typing import Any, Dict

from .state import STATE


def estimate_hours() -> Dict[str, Any]:
    summary = {}
    total_hours = 0.0

    for code, course in STATE["courses"].items():
        materials = course.get("materials", [])
        hours = max(1.0, len(materials) * 2.0)
        hours = round(hours, 2)
        course["estimated_hours"] = hours
        summary[code] = {"estimated_hours": hours, "materials": len(materials)}
        total_hours += hours

    return {"ok": True, "total_hours": round(total_hours, 2), "courses": summary}

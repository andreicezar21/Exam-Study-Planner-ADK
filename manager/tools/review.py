from typing import Any, Dict, List

from .state import STATE


def review_plan() -> Dict[str, Any]:
    plan = STATE.get("study_plan") or []
    prefs = STATE.get("preferences", {})
    daily_max = float(prefs.get("daily_max_hours", 3.0))

    if not plan:
        return {"ok": False, "message": "No plan found. Build a plan first."}

    warnings: List[str] = []
    for day in plan:
        if day.get("total_hours", 0) > daily_max + 1e-6:
            warnings.append(
                f"{day.get('date')} exceeds daily max ({day.get('total_hours')}h > {daily_max}h)"
            )

    return {"ok": True, "warnings": warnings}

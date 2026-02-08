from pathlib import Path
from typing import Any, Dict, List

from .state import STATE, _ensure_course
from .utils import extract_course_codes, extract_file_paths, resolve_path


def ingest_request(request: str) -> Dict[str, Any]:
    paths = extract_file_paths(request)
    if not paths:
        return {
            "ok": False,
            "message": "Provide PDF paths or file names ending in .pdf.",
        }

    search_dirs = _default_search_dirs()
    ingested: List[str] = []
    missing: List[str] = []

    for candidate in paths:
        resolved = resolve_path(candidate, search_dirs)
        path_str = str(resolved) if resolved else candidate

        if resolved is None and not candidate.lower().endswith(".pdf"):
            missing.append(candidate)
            continue

        code = _guess_course_code(candidate)
        course = _ensure_course(code)
        course["materials"].append({"path": path_str})
        ingested.append(path_str)

    result: Dict[str, Any] = {"ok": True, "ingested": ingested, "missing": missing}
    if missing:
        result["message"] = "Some files were not found. Provide full paths for missing files."
    return result


def _guess_course_code(text: str) -> str:
    codes = extract_course_codes(text)
    if codes:
        return codes[0]
    return f"COURSE-{len(STATE['courses']) + 1}"


def _default_search_dirs() -> List[Path]:
    home = Path.home()
    candidates = [
        Path.cwd(),
        home / "Downloads",
        home / "Documents",
    ]
    return [c for c in candidates if c.exists()]

# Exam Study Planner (ADK)

A 5-agent AI workflow built with Google ADK that creates custom study plans from evaluations, course syllabi, exam overviews, and class textbooks. It ingests materials, extracts midterm coverage, estimates workload when requested, and produces a day-by-day plan you can export and reuse.

## Features
- 5 specialist agents coordinated by a manager: ingestion, estimation, planning, review, and greeting.
- Upload-aware ingestion with artifact citation, PDF sampling for large files, and strict no-hallucination guardrails.
- Midterm-focused summaries with relative dates converted to absolute dates.
- Optional study-time estimation based on textbook and coverage details.
- Day-by-day CSV plan output for easy import into calendars or spreadsheets.
- Optional review step that checks conflicts, hours-per-day limits, and post-midterm tasks.
- Built-in tooling for inline data sanitization, artifact memory, and current-date injection.

## Project Structure
- `manager/agent.py` — Manager agent that orchestrates the workflow.
- `manager/sub_agents/` — Ingestion, estimation, planning, review, and greeting agents.
- `manager/tools/` — Custom tools for artifact memory, PDF extraction, date handling, sanitization, and plan export.

## Setup
1. Create and activate a virtual environment:
   - `python -m venv .venv`
   - `./.venv/Scripts/Activate.ps1`
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Create `manager/.env` from `manager/.env.example` and fill in your API key.
4. Run the ADK web UI:
   - `adk web`

## Notes
- Natural language dates are supported (e.g., "in 5 days", "next Tuesday") and are converted to absolute dates.
- Only `manager/.env.example` is committed; `manager/.env` stays local.

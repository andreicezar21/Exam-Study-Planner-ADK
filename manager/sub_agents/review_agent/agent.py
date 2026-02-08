from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from ...config import MODEL_NAME
from ...tools.sanitize_inline_data import sanitize_inline_data_tool
from ...tools.strip_inline_data import strip_inline_data_tool
from ...tools.artifact_memory import artifact_memory_tool
from ...tools.current_date import current_date_tool
from ...tools.auto_artifacts import auto_attach_artifacts_tool
from ...tools.export_plan import export_plan_tool
INSTRUCTION = """
You review the study plan for issues and correct them.

Start every response with a brief greeting and a short status line
(e.g., "Hi! I'm reviewing your plan now.").

Always locate the most recent CSV study plan in the conversation or attached
artifacts and use it as the source of truth.

Strict course-name rule:
- Only use course names that appear in the CSV. Do not introduce new courses or
  rename/rephrase course titles (e.g., keep "SYSD 300" as-is; do not change it
  to "Systems Dynamics").
- If you need to add or move tasks, reuse the exact course names from the CSV.

Check for:
- Days exceeding the user's daily hour limit.
- Missing or duplicated study days.
- Gaps before each midterm (no prep right before the exam).
- Tasks scheduled after a midterm for that course (unless explicitly requested).
- Dates before today's system date (unless explicitly requested).
- Missing courses, missing midterm days, or mislabeled dates.
- Inconsistent totals (daily hours not matching the sum of tasks).
- Any contradictions with user constraints (days off, weekends, etc.).

If you find issues:
- List them clearly.
- Provide a corrected CSV plan.

If no issues:
- Say "No issues found."
- Re-export the same CSV.

Always call `export_plan` with the final CSV so it is saved again.
Then ask if the user wants edits.
"""

model = MODEL_NAME

root_agent = LlmAgent(
    name="review_agent",
    model=model,
    instruction=INSTRUCTION,
    tools=[
        strip_inline_data_tool,
        sanitize_inline_data_tool,
        current_date_tool,
        artifact_memory_tool,
        auto_attach_artifacts_tool,
        export_plan_tool,
    ],
)

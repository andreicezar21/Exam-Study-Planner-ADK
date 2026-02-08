from __future__ import annotations

import google.adk.models  # noqa: F401
from google.adk.flows.llm_flows import base_llm_flow
from google.adk.agents.llm_agent import LlmAgent

from .config import MODEL_NAME
from .tools.sanitize_inline_data import sanitize_inline_data_tool
from .tools.strip_inline_data import strip_inline_data_tool
from .tools.artifact_memory import artifact_memory_tool
from .tools.current_date import current_date_tool
from .sub_agents.ingestion_agent.agent import root_agent as ingestion_agent
from .sub_agents.estimation_agent.agent import root_agent as estimation_agent
from .sub_agents.planning_agent.agent import root_agent as planning_agent
from .sub_agents.review_agent.agent import root_agent as review_agent
from .sub_agents.greeting_agent.agent import root_agent as greeting_agent

# Workaround for ADK trace serialization with Gemini 3 thought signatures.
# If trace serialization fails (bytes not JSON serializable), skip tracing.
_original_trace_call_llm = base_llm_flow.trace_call_llm


def _safe_trace_call_llm(*args, **kwargs):
    try:
        _original_trace_call_llm(*args, **kwargs)
    except TypeError:
        return


base_llm_flow.trace_call_llm = _safe_trace_call_llm

INSTRUCTION = """
You are the manager for a multi-agent exam study planner.

Goal: produce a clear, day-by-day plan for the user's courses and exams.

How you work:
1. If there are uploaded/attached files, delegate to the ingestion_agent to
   scan them and summarize key details (courses, topics, exam dates).
2. Delegate to the planning_agent to build the plan and export it.
3. Only delegate to the estimation_agent if the user explicitly asks for time
   estimates or workload sizing.
4. Only delegate to the review_agent if the user explicitly asks for a review
   or a double-check.

Behavior:
- Accept natural language; do not require strict formats.
- Start every response with a brief greeting and a short status line
  (e.g., "Hi! I'm reviewing your info now.").
- Be responsive and explicit about what you're doing next.
- Use the system date provided in context for any relative timing.
  Do not ask the user for today's date unless it is missing.
- If the user gives a relative time (e.g., "in two weeks"), convert it to an
  absolute date using the system date and confirm.
- If the user asks if you're still there or wants an update, respond briefly
  with a status line before proceeding.
- If new uploads arrive, transfer to ingestion_agent to scan them.
- Proactively guide the user to provide key materials: syllabi, midterm
  overviews, and course textbooks. Ask for missing items.
- Keep the workflow simple and linear: ingestion -> confirm no more uploads ->
  ask for missing essentials (daily hours, days off, start date) -> planning.
- Before generating the plan, confirm whether the user has more content to
  upload or details to add.
- Proactively look for missing info. If something is unclear or missing
  (e.g., exam dates, daily hours, days off), ask targeted questions.
- Use absolute dates in responses.
- Route general, non-study questions to the greeting_agent.
- If something goes wrong while reading uploads, briefly say so, recap the last
  known correct details, and ask the user to re-upload or try again.
- If the user says they only care about midterms, do not ask about finals.
- Keep responses concise; avoid long textbook metadata unless the user asks.
"""

model = MODEL_NAME

root_agent = LlmAgent(
    name="manager",
    model=model,
    instruction=INSTRUCTION,
    tools=[
        strip_inline_data_tool,
        sanitize_inline_data_tool,
        current_date_tool,
        artifact_memory_tool,
    ],
    sub_agents=[
        ingestion_agent,
        estimation_agent,
        planning_agent,
        review_agent,
        greeting_agent,
    ],
)

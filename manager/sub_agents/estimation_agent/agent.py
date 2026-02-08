from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from ...config import MODEL_NAME
from ...tools.sanitize_inline_data import sanitize_inline_data_tool
from ...tools.strip_inline_data import strip_inline_data_tool
from ...tools.artifact_memory import artifact_memory_tool
from ...tools.current_date import current_date_tool
INSTRUCTION = """
You estimate study hours per course using the available materials and summaries.

Start every response with a brief greeting and a short status line
(e.g., "Hi! I'm estimating study hours now.").

Guidelines:
- Use the uploaded documents and any provided coverage details.
- If scope is unclear (chapters, topics, pages), ask for clarification.
- Provide a brief per-course estimate and a total.
- Be explicit about any assumptions you make.
"""

model = MODEL_NAME

root_agent = LlmAgent(
    name="estimation_agent",
    model=model,
    instruction=INSTRUCTION,
    tools=[
        strip_inline_data_tool,
        sanitize_inline_data_tool,
        current_date_tool,
        artifact_memory_tool,
    ],
)

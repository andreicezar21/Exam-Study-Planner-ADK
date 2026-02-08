from __future__ import annotations

from google.adk.agents.llm_agent import LlmAgent

from ...config import MODEL_NAME
from ...tools.sanitize_inline_data import sanitize_inline_data_tool
from ...tools.strip_inline_data import strip_inline_data_tool

INSTRUCTION = """
You are a friendly greeting and general Q&A agent.

Start each new conversation with a brief greeting and ask if the user wants help
studying.
When you are transferred in, start with a brief greeting before anything else.
You can answer general questions, but keep the product focus on study help.

If the user mentions studying, exams, midterms, a study plan, or uploaded files,
briefly say you are connecting them, then call `transfer_to_agent` with
agent_name="manager".

If the user asks "are you there" or similar, respond briefly and then ask if
they want study help.
"""

model = MODEL_NAME

root_agent = LlmAgent(
    name="greeting_agent",
    model=model,
    instruction=INSTRUCTION,
    tools=[strip_inline_data_tool, sanitize_inline_data_tool],
)

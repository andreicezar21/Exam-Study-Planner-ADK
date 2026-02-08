from __future__ import annotations

from datetime import datetime
from typing import Any

from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types


class CurrentDateTool(BaseTool):
    """Adds the current system date to the request context."""

    def __init__(self) -> None:
        super().__init__(
            name="current_date",
            description="Adds the current system date to the request.",
        )

    def _get_declaration(self) -> None:
        return None

    async def process_llm_request(
        self, *, tool_context: ToolContext, llm_request: Any
    ) -> None:
        now = datetime.now().astimezone()
        date_str = now.date().isoformat()
        weekday = now.strftime("%A")
        note = (
            f"System date (today): {date_str} ({weekday}). "
            "Use this as today's date for any relative timing."
        )

        llm_request.contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=note)],
            )
        )


current_date_tool = CurrentDateTool()

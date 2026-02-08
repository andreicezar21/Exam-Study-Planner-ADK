from __future__ import annotations

from typing import Any

from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext


class SanitizeInlineDataTool(BaseTool):
    """Remove empty inline_data parts to avoid INVALID_ARGUMENT errors."""

    def __init__(self) -> None:
        super().__init__(
            name="sanitize_inline_data",
            description="Strips empty inline_data parts from requests.",
        )

    def _get_declaration(self):
        # No function declaration; this is a preprocessing-only tool.
        return None

    async def process_llm_request(
        self, *, tool_context: ToolContext, llm_request: Any
    ) -> None:
        contents = getattr(llm_request, "contents", None)
        if not contents:
            return

        for content in contents:
            parts = getattr(content, "parts", None)
            if not parts:
                continue
            filtered = []
            for part in parts:
                inline = getattr(part, "inline_data", None)
                if inline is None:
                    filtered.append(part)
                    continue
                data = getattr(inline, "data", None)
                # Drop inline_data parts with no bytes.
                if data:
                    filtered.append(part)
            content.parts = filtered


sanitize_inline_data_tool = SanitizeInlineDataTool()

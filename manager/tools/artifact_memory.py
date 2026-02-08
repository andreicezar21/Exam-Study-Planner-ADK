from __future__ import annotations

from typing import Any, List

from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

MAX_ITEMS = 15
MAX_SUMMARY_CHARS = 600
MAX_TOTAL_CHARS = 4000


class ArtifactMemoryTool(BaseTool):
    """Adds cached upload summaries to the request so uploads can be recalled."""

    def __init__(self) -> None:
        super().__init__(
            name="artifact_memory",
            description="Adds cached upload summaries to the request.",
        )

    def _get_declaration(self) -> None:
        return None

    async def process_llm_request(
        self, *, tool_context: ToolContext, llm_request: Any
    ) -> None:
        state = tool_context.state
        summaries = state.get("_artifact_summaries")
        if not isinstance(summaries, dict):
            summaries = {}

        upload_index = state.get("_upload_index")
        if not isinstance(upload_index, dict):
            upload_index = {}

        upload_order = state.get("_upload_order")
        if not isinstance(upload_order, list):
            upload_order = list(upload_index.keys())

        artifact_names: List[str] = []
        try:
            artifact_names = tool_context.list_artifacts()
        except Exception:
            artifact_names = []

        if not summaries and not upload_index and not artifact_names:
            return

        lines: List[str] = []
        total = 0

        def add_line(line: str) -> None:
            nonlocal total
            if len(lines) >= MAX_ITEMS:
                return
            if total + len(line) + 1 > MAX_TOTAL_CHARS:
                return
            lines.append(line)
            total += len(line) + 1

        for sha in upload_order:
            meta = upload_index.get(sha)
            if not meta:
                continue
            name = meta.get("name", "unknown")
            mime = meta.get("mime", "")
            size = meta.get("bytes")
            line = f"- {name}"
            extras = []
            if mime:
                extras.append(mime)
            if size is not None:
                extras.append(f"{size} bytes")
            if extras:
                line += f" ({', '.join(extras)})"

            summary = summaries.get(name)
            if isinstance(summary, str) and summary:
                short = summary.replace("\n", " ")
                if len(short) > MAX_SUMMARY_CHARS:
                    short = short[:MAX_SUMMARY_CHARS] + "..."
                line += f" | Summary: {short}"

            add_line(line)

        if not lines and summaries:
            for name, summary in summaries.items():
                short = summary.replace("\n", " ")
                if len(short) > MAX_SUMMARY_CHARS:
                    short = short[:MAX_SUMMARY_CHARS] + "..."
                add_line(f"- {name} | Summary: {short}")
                if len(lines) >= MAX_ITEMS:
                    break

        if not lines and artifact_names:
            for name in artifact_names[:MAX_ITEMS]:
                add_line(f"- {name}")

        if not lines:
            return

        text = "Session uploads (cached for this session):\n" + "\n".join(lines)
        llm_request.contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=text)],
            )
        )


artifact_memory_tool = ArtifactMemoryTool()

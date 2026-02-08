from __future__ import annotations

import hashlib
from typing import Any, List

from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

_MAX_NOTE_NAMES = 3


def _guess_extension(mime: str) -> str:
    if not mime:
        return ""
    lower = mime.lower()
    if "pdf" in lower:
        return ".pdf"
    if "json" in lower:
        return ".json"
    if "csv" in lower:
        return ".csv"
    if "text" in lower or "plain" in lower:
        return ".txt"
    if "png" in lower:
        return ".png"
    if "jpeg" in lower or "jpg" in lower:
        return ".jpg"
    if "zip" in lower:
        return ".zip"
    return ""


def _init_upload_state(tool_context: ToolContext) -> tuple[dict, list]:
    upload_index = tool_context.state.get("_upload_index")
    if not isinstance(upload_index, dict):
        upload_index = {}
    upload_order = tool_context.state.get("_upload_order")
    if not isinstance(upload_order, list):
        upload_order = []
    return upload_index, upload_order


class StripInlineDataTool(BaseTool):
    """Strip inline_data parts to avoid large or invalid requests.

    Also persists uploads to session artifacts so they can be reused later.
    """

    def __init__(self) -> None:
        super().__init__(
            name="strip_inline_data",
            description=(
                "Removes inline_data parts from requests and stores uploads."
            ),
        )

    def _get_declaration(self) -> None:
        # No function declaration; preprocessing-only tool.
        return None

    async def process_llm_request(
        self, *, tool_context: ToolContext, llm_request: Any
    ) -> None:
        contents = getattr(llm_request, "contents", None)
        if not contents:
            return

        upload_index, upload_order = _init_upload_state(tool_context)

        removed = 0
        saved = 0
        failed = 0
        saved_names: List[str] = []

        for content in contents:
            parts = getattr(content, "parts", None)
            if not parts:
                continue
            kept = []
            for part in parts:
                inline = getattr(part, "inline_data", None)
                if inline is None:
                    kept.append(part)
                    continue

                removed += 1
                data = getattr(inline, "data", None)
                mime = getattr(inline, "mime_type", "") or ""
                if not data:
                    continue

                sha = hashlib.sha256(data).hexdigest()
                if sha in upload_index:
                    continue

                ext = _guess_extension(mime)
                filename = f"upload_{sha[:12]}{ext}"

                if any(meta.get("name") == filename for meta in upload_index.values()):
                    suffix = 1
                    base = filename[:-len(ext)] if ext else filename
                    while any(
                        meta.get("name") == f"{base}_{suffix}{ext}"
                        for meta in upload_index.values()
                    ):
                        suffix += 1
                    filename = f"{base}_{suffix}{ext}"

                try:
                    tool_context.save_artifact(filename=filename, artifact=part)
                except Exception:
                    failed += 1
                    continue

                upload_index[sha] = {
                    "name": filename,
                    "mime": mime,
                    "bytes": len(data),
                    "sha": sha,
                }
                if sha not in upload_order:
                    upload_order.append(sha)
                saved += 1
                saved_names.append(filename)

            content.parts = kept

        if removed:
            tool_context.state["_upload_index"] = upload_index
            tool_context.state["_upload_order"] = upload_order
            tool_context.state["_last_upload_saved"] = saved
            if saved_names:
                tool_context.state["_last_upload_names"] = saved_names

            note = (
                f"Note: {removed} uploaded file(s) were saved to this session "
                "and stripped from the request payload. "
                "You can reference these uploads later in this session; "
                "use ingestion_agent to scan them when needed."
            )
            if failed:
                note += " Some uploads could not be saved."
            if saved_names:
                preview = ", ".join(saved_names[:_MAX_NOTE_NAMES])
                if len(saved_names) > _MAX_NOTE_NAMES:
                    preview += ", ..."
                note += f" Saved: {preview}."

            llm_request.contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=note)],
                )
            )
            tool_context.state["_inline_data_stripped_last"] = removed


strip_inline_data_tool = StripInlineDataTool()

from __future__ import annotations

from io import BytesIO
from typing import Any, Iterable

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None

from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

MAX_ATTACH_BYTES = 1_000_000


class AutoAttachArtifactsTool(BaseTool):
    """Automatically attach small artifacts to the LLM request once per session.

    PDFs are not attached; a summary is used instead.
    """

    def __init__(self) -> None:
        super().__init__(
            name="auto_attach_artifacts",
            description="Automatically attaches uploaded artifacts to the request.",
        )

    def _get_declaration(self) -> types.FunctionDeclaration | None:
        # No function declaration; this tool does not use model function calling.
        return None

    async def process_llm_request(
        self, *, tool_context: ToolContext, llm_request: Any
    ) -> None:
        artifact_names = tool_context.list_artifacts()
        if not artifact_names:
            return

        attached = _get_attached_set(tool_context.state.get("_artifacts_attached"))
        to_attach = [name for name in artifact_names if name not in attached]
        if not to_attach:
            return

        for name in to_attach:
            artifact = tool_context.load_artifact(name)
            if artifact is None:
                continue
            inline = getattr(artifact, "inline_data", None)
            mime = getattr(inline, "mime_type", "") if inline else ""
            data = getattr(inline, "data", None) if inline else None

            if inline and "pdf" in mime.lower() and data:
                pages = _safe_page_count(data) if PdfReader is not None else None
                page_note = f"{pages} pages" if pages is not None else "page count unknown"
                llm_request.contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(
                                text=(
                                    f"Artifact {name} is a PDF ({page_note}, "
                                    f"{len(data)} bytes). A compact summary will be used "
                                    "instead of attaching the full file."
                                )
                            )
                        ],
                    )
                )
                attached.add(name)
                continue

            if data is not None and len(data) > MAX_ATTACH_BYTES:
                llm_request.contents.append(
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(
                                text=(
                                    f"Artifact {name} is {mime or 'a file'} "
                                    f"({len(data)} bytes). It is too large to attach "
                                    "directly; use summaries or request specific sections."
                                )
                            )
                        ],
                    )
                )
                attached.add(name)
                continue

            llm_request.contents.append(
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=f"Artifact {name} is:"),
                        artifact,
                    ],
                )
            )
            attached.add(name)

        tool_context.state["_artifacts_attached"] = sorted(attached)


def _get_attached_set(value: Any) -> set[str]:
    if isinstance(value, list):
        return {str(v) for v in value}
    if isinstance(value, set):
        return {str(v) for v in value}
    return set()


def _safe_page_count(data: bytes) -> int | None:
    try:
        reader = PdfReader(BytesIO(data))
        return len(reader.pages)
    except Exception:
        return None


auto_attach_artifacts_tool = AutoAttachArtifactsTool()

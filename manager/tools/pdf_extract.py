from __future__ import annotations

from io import BytesIO
from typing import Any, List

from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None

KEYWORDS = [
    "midterm",
    "exam",
    "final",
    "schedule",
    "syllabus",
    "overview",
    "chapter",
    "week",
    "grading",
    "assessment",
]

FIRST_PAGES = 5
MAX_SCAN_PAGES = 200
MAX_EXCERPT_CHARS = 1200
MAX_TOTAL_CHARS = 8000
LARGE_PAGE_THRESHOLD = 200
LARGE_BYTES_THRESHOLD = 10_000_000
LARGE_FIRST_PAGES = 8
LARGE_MAX_TOTAL_CHARS = 4000
SUMMARY_KEY = "_artifact_summaries"


class PdfExtractTool(BaseTool):
    """Extracts a compact text digest from uploaded PDFs for large files."""

    def __init__(self) -> None:
        super().__init__(
            name="pdf_extract",
            description="Extracts key text snippets from uploaded PDFs.",
        )

    def _get_declaration(self):
        return None

    async def process_llm_request(
        self, *, tool_context: ToolContext, llm_request: Any
    ) -> None:
        if PdfReader is None:
            return

        artifact_names = tool_context.list_artifacts()
        if not artifact_names:
            return

        summaries = tool_context.state.get(SUMMARY_KEY)
        if not isinstance(summaries, dict):
            summaries = {}

        for name in artifact_names:
            if name in summaries:
                continue

            part = tool_context.load_artifact(name)
            if part is None:
                continue

            inline = getattr(part, "inline_data", None)
            if inline is None:
                continue
            mime = getattr(inline, "mime_type", "") or ""
            if "pdf" not in mime.lower():
                continue
            data = getattr(inline, "data", None)
            if not data:
                continue

            digest = _build_pdf_digest(name, data)
            if not digest:
                continue

            summaries[name] = digest
            llm_request.contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=digest)],
                )
            )

        if summaries:
            tool_context.state[SUMMARY_KEY] = summaries


def _build_pdf_digest(name: str, data: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(data))
    except Exception:
        return (
            f"Artifact {name} is a PDF, but text extraction failed. "
            "It may be scanned; please provide a text-based version or key dates."
        )

    num_pages = len(reader.pages)
    size_bytes = len(data)
    is_large = num_pages > LARGE_PAGE_THRESHOLD or size_bytes > LARGE_BYTES_THRESHOLD

    if is_large:
        pages_to_check = list(range(min(LARGE_FIRST_PAGES, num_pages)))
        extra = []
        if num_pages > LARGE_FIRST_PAGES:
            extra.append(num_pages // 2)
            extra.append(num_pages - 1)
            extra.append(num_pages // 4)
        for idx in extra:
            if 0 <= idx < num_pages:
                pages_to_check.append(idx)
        pages_to_check = sorted(set(pages_to_check))
    else:
        pages_to_check = list(range(min(FIRST_PAGES, num_pages)))
        scan_limit = min(num_pages, MAX_SCAN_PAGES)
        for i in range(scan_limit):
            if i in pages_to_check:
                continue
            text = _safe_extract(reader, i)
            if not text:
                continue
            if _has_keyword(text):
                pages_to_check.append(i)

        pages_to_check = sorted(set(pages_to_check))[:MAX_SCAN_PAGES]

    snippets: List[str] = []
    total = 0
    max_total = LARGE_MAX_TOTAL_CHARS if is_large else MAX_TOTAL_CHARS
    for i in pages_to_check:
        text = _safe_extract(reader, i)
        if not text:
            continue
        snippet = text.strip().replace("\x00", " ")
        snippet = " ".join(snippet.split())
        if len(snippet) > MAX_EXCERPT_CHARS:
            snippet = snippet[:MAX_EXCERPT_CHARS] + "..."
        entry = f"[Page {i+1}] {snippet}"
        if total + len(entry) > max_total:
            break
        snippets.append(entry)
        total += len(entry)

    if not snippets:
        return (
            f"Artifact {name} is a PDF with {num_pages} pages. "
            "Text extraction returned no usable content."
        )

    sampled_note = ""
    if is_large:
        sampled_note = " (sampled key pages; large PDF)"
    elif num_pages > MAX_SCAN_PAGES:
        sampled_note = f" (sampled first {MAX_SCAN_PAGES} pages)"

    return (
        f"Artifact {name} summary: {num_pages} pages{sampled_note}.\n"
        + "\n".join(snippets)
    )


def _safe_extract(reader: PdfReader, page_index: int) -> str:
    try:
        return reader.pages[page_index].extract_text() or ""
    except Exception:
        return ""


def _has_keyword(text: str) -> bool:
    lower = text.lower()
    return any(k in lower for k in KEYWORDS)


pdf_extract_tool = PdfExtractTool()

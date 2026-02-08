from __future__ import annotations

from pathlib import Path
from typing import Any

from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.genai import types


class ExportPlanTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="export_plan",
            description="Save the study plan to a Markdown or CSV file.",
        )

    def _get_declaration(self) -> types.FunctionDeclaration | None:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "format": types.Schema(
                        type=types.Type.STRING,
                        description="markdown or csv",
                    ),
                    "content": types.Schema(
                        type=types.Type.STRING,
                        description="The full study plan in the chosen format.",
                    ),
                },
                required=["content"],
            ),
        )

    async def run_async(
        self, *, args: dict[str, Any], tool_context: ToolContext
    ) -> Any:
        raw_format = (args.get("format") or "csv").lower()
        content = args.get("content") or ""
        if raw_format in ("csv",):
            ext = "csv"
            mime = "text/csv"
        else:
            ext = "md"
            mime = "text/markdown"

        output_dir = Path.cwd() / "outputs"
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"study_plan.{ext}"
        path = output_dir / filename
        path.write_text(content, encoding="utf-8")

        artifact_part = types.Part.from_bytes(
            data=content.encode("utf-8"),
            mime_type=mime,
        )
        tool_context.save_artifact(filename, artifact_part)

        return {"ok": True, "path": str(path), "artifact": filename, "format": ext}


export_plan_tool = ExportPlanTool()

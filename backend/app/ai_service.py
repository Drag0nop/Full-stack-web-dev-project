import json
from typing import Any

import google.generativeai as genai

from .config import get_settings

settings = get_settings()


class DocumentationService:
    def __init__(self) -> None:
        self.model_name = "gemini-1.5-flash"
        self.enabled = bool(settings.gemini_api_key)
        if self.enabled:
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None

    def document_repository(self, repo_data: dict[str, Any]) -> dict[str, Any]:
        if self.enabled and self.model is not None:
            try:
                return self._document_with_gemini(repo_data)
            except Exception:
                pass
        return self._fallback_documentation(repo_data)

    def answer_question(self, question: str, project_payload: dict[str, Any]) -> str:
        if self.enabled and self.model is not None:
            try:
                prompt = (
                    "You are answering questions about a codebase. Use the repository overview and file summaries "
                    "below to answer accurately. If unsure, say what context is missing.\n\n"
                    f"Question:\n{question}\n\n"
                    f"Project context:\n{json.dumps(project_payload)[:18000]}"
                )
                response = self.model.generate_content(prompt)
                return (response.text or "").strip()
            except Exception:
                pass
        overview = project_payload.get("overview_markdown", "")
        file_names = ", ".join(file["path"] for file in project_payload.get("files", [])[:10])
        return (
            f"Question: {question}\n\n"
            f"Repository overview:\n{overview}\n\n"
            f"Available files I can reference include: {file_names}.\n"
            "Gemini is not configured, so this response is based on parsed structure and generated summaries."
        )

    def _document_with_gemini(self, repo_data: dict[str, Any]) -> dict[str, Any]:
        prompt = (
            "You are generating documentation for a software repository. Return valid JSON with this exact shape: "
            '{"overview_markdown": string, "files": [{"path": string, "summary_markdown": string}]}. '
            "For each file, explain purpose, key logic, and notable symbols. Repository data:\n"
            f"{json.dumps(repo_data)[:25000]}"
        )
        response = self.model.generate_content(prompt)
        payload = json.loads(response.text)
        file_map = {item["path"]: item["summary_markdown"] for item in payload.get("files", [])}
        enriched_files = []
        for file_entry in repo_data["files"]:
            enriched_files.append(
                {
                    **file_entry,
                    "summary_markdown": file_map.get(file_entry["path"], self._fallback_file_summary(file_entry)),
                }
            )
        return {"overview_markdown": payload.get("overview_markdown", ""), "files": enriched_files}

    def _fallback_file_summary(self, file_entry: dict[str, Any]) -> str:
        symbols = file_entry.get("symbols", [])
        symbol_lines = []
        for symbol in symbols[:10]:
            name = symbol.get("name", "unknown")
            symbol_type = symbol.get("type", "symbol")
            symbol_lines.append(f"- `{name}` ({symbol_type})")
        symbol_section = "\n".join(symbol_lines) if symbol_lines else "- No top-level symbols extracted."
        return (
            f"### Purpose\n"
            f"`{file_entry['path']}` is a {file_entry['language']} file included in the uploaded repository.\n\n"
            f"### Key symbols\n{symbol_section}\n\n"
            f"### Preview\n"
            f"```{file_entry['language']}\n{file_entry['content_preview'][:1200]}\n```"
        )

    def _fallback_documentation(self, repo_data: dict[str, Any]) -> dict[str, Any]:
        files = []
        for entry in repo_data["files"]:
            files.append({**entry, "summary_markdown": self._fallback_file_summary(entry)})
        metadata = repo_data["metadata"]
        overview = (
            f"# Repository Overview\n\n"
            f"This upload contains **{metadata['file_count']} files** across the following detected formats: "
            f"{', '.join(metadata['languages']) or 'unknown'}.\n\n"
            f"The parser extracted **{metadata['python_file_count']} Python files** and built a navigable tree "
            f"plus top-level symbol metadata for each supported source file.\n\n"
            f"Gemini is {'configured' if self.enabled else 'not configured'}, so "
            f"{'these summaries were AI-generated.' if self.enabled else 'the current summaries are heuristic fallbacks.'}"
        )
        return {"overview_markdown": overview, "files": files}

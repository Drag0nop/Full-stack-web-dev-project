import ast
import os
import re
import time

import requests

from app.core.config import settings

GEMINI_API_KEY = settings.GEMINI_API_KEY

# Use only models the user's API key explicitly supports.
API_VERSION = "v1beta"
MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]

MAX_CHARS = 6000
MAX_REPO_SUMMARY_CHARS = 14000
MAX_REPO_FILES = 120
MAX_RETRIES = 3
RETRY_DELAY = 2
REQUEST_TIMEOUT = 30

LAST_GEMINI_ERROR = ""

SYSTEM_CONTEXT = """
You are a senior software architect and technical writer.

Your job is to:
- Understand repository structure
- Infer architecture from code
- Generate professional documentation

Focus on clarity, structure, and practical usefulness.
"""


def _extract_text(data: dict):
    candidates = data.get("candidates") or []
    for candidate in candidates:
        content = candidate.get("content") or {}
        parts = content.get("parts") or []
        texts = [part.get("text", "").strip() for part in parts if part.get("text")]
        if texts:
            return "\n".join(texts).strip()
    return None


def _post(url: str, payload: dict):
    # Avoid broken system proxy settings blocking Gemini requests.
    with requests.Session() as session:
        session.trust_env = False
        return session.post(url, json=payload, timeout=REQUEST_TIMEOUT)


def call_gemini(prompt: str):
    global LAST_GEMINI_ERROR
    LAST_GEMINI_ERROR = ""

    if not GEMINI_API_KEY:
        LAST_GEMINI_ERROR = "Missing GEMINI_API_KEY"
        return None

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.4,
            "topP": 0.8,
        },
    }

    for model in MODELS:
        url = (
            f"https://generativelanguage.googleapis.com/{API_VERSION}/models/"
            f"{model}:generateContent?key={GEMINI_API_KEY}"
        )

        for _attempt in range(MAX_RETRIES):
            try:
                res = _post(url, payload)

                if res.status_code == 200:
                    text = _extract_text(res.json())
                    if text:
                        return text
                    LAST_GEMINI_ERROR = f"{model} returned an empty response"
                    break

                if res.status_code in (429, 503):
                    LAST_GEMINI_ERROR = f"{model} rate-limited or unavailable ({res.status_code})"
                    time.sleep(RETRY_DELAY)
                    continue

                LAST_GEMINI_ERROR = f"{model} failed: {res.text}"
                break
            except Exception as exc:
                LAST_GEMINI_ERROR = f"Gemini request failed: {exc}"
                time.sleep(RETRY_DELAY)

    return None


def chunk_code(code: str):
    chunks = []
    current = ""

    for line in code.split("\n"):
        if len(current) + len(line) < MAX_CHARS:
            current += line + "\n"
        else:
            chunks.append(current)
            current = line + "\n"

    if current:
        chunks.append(current)

    return chunks


def prioritize_chunks(chunks):
    keywords = ["main", "app", "agent", "service", "controller", "model", "route"]

    def score(chunk):
        return sum(keyword in chunk.lower() for keyword in keywords)

    return sorted(chunks, key=score, reverse=True)


def analyze_chunks(chunks):
    results = []

    for chunk in chunks:
        prompt = SYSTEM_CONTEXT + f"""

Analyze this code chunk at a system-design level.

Focus on:
- Role of this code
- Component type
- Responsibilities
- Interactions with the rest of the system

Avoid low-level explanations.

Chunk:
{chunk}
"""
        result = call_gemini(prompt)
        if result:
            results.append(result)

    return results


def generate_readme(summaries, components=None):
    combined = "\n\n".join(summaries)

    prompt = SYSTEM_CONTEXT + f"""

Generate a professional GitHub README for this repository.

Strict rules:
- Do not assume domain unless strongly supported by the code.
- Infer purpose from code structure and responsibilities.
- Keep it practical and precise.

Output format:

# Project Overview

# Architecture

# Key Components

# Data Flow

# Setup & Usage

# Improvements & Future Work

Code analysis:
{combined}

Additional component grouping:
{components if components else "N/A"}
"""

    return call_gemini(prompt)


def analyze_code(code: str):
    if not GEMINI_API_KEY:
        return fallback_analysis(code)

    chunks = prioritize_chunks(chunk_code(code))[:5]
    summaries = analyze_chunks(chunks)

    if not summaries:
        return {
            "analysis": (
                "AI code analysis failed.\n\n"
                f"Last Gemini error:\n{LAST_GEMINI_ERROR or 'Unknown error'}"
            ),
            "type": "error",
        }

    readme = generate_readme(summaries)
    if not readme:
        return {
            "analysis": (
                "README generation failed after code analysis.\n\n"
                f"Last Gemini error:\n{LAST_GEMINI_ERROR or 'Unknown error'}"
            ),
            "type": "error",
        }

    return {
        "analysis": readme,
        "type": "success",
        "chunks": len(chunks),
    }


def fallback_analysis(code: str):
    lines = len(code.splitlines())
    functions = code.count("def ")
    classes = code.count("class ")
    return {
        "analysis": (
            "Fallback Analysis\n\n"
            f"- Lines: {lines}\n"
            f"- Functions: {functions}\n"
            f"- Classes: {classes}\n"
        ),
        "type": "fallback",
    }


def summarize_readme(readme_text: str, repo_url: str = ""):
    if not GEMINI_API_KEY:
        excerpt = readme_text[:1200].strip()
        return {
            "analysis": (
                "README Summary\n\n"
                f"{excerpt}\n\n"
                "Suggested Improvements:\n"
                "- Add clearer setup and environment configuration steps.\n"
                "- Include usage examples and troubleshooting notes.\n"
                "- Document testing, deployment, and roadmap items."
            ),
            "type": "fallback",
        }

    prompt = f"""
You are a senior product-minded software architect.

Read this repository README and produce:

## Summary
A concise explanation of what the project does, who it is for, and how it works.

## Suggested Improvements
Concrete improvements across product, engineering, documentation, testing, security, and future enhancements.

Keep the answer practical and specific to the README content.

Repository: {repo_url or "N/A"}

README:
{readme_text[:12000]}
"""

    result = call_gemini(prompt)
    return {
        "analysis": result or (
            "README summarization failed.\n\n"
            f"Last Gemini error:\n{LAST_GEMINI_ERROR or 'Unknown error'}"
        ),
        "type": "readme_summary",
    }


def _extract_python_ast(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file_obj:
            tree = ast.parse(file_obj.read())
    except Exception:
        return None

    imports = []
    funcs = []
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names[:4])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        elif isinstance(node, ast.FunctionDef):
            funcs.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)

    return {
        "imports": sorted(set(imports))[:8],
        "functions": funcs[:8],
        "classes": classes[:6],
    }


def _extract_non_python_signatures(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file_obj:
            content = file_obj.read(12000)
    except Exception:
        return []

    patterns = [
        r"\bclass\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"\bfunction\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\([^)]*\)\s*\{",
    ]

    names = []
    for pattern in patterns:
        names.extend(re.findall(pattern, content))

    return [name for name in names if len(name) > 2][:10]


def build_repo_ast_summary(repo_path):
    ignore = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"}
    allowed = {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".cpp", ".c", ".go", ".rs"}

    lines = []
    count = 0

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [dir_name for dir_name in dirs if dir_name not in ignore]

        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext not in allowed:
                continue

            count += 1
            if count > MAX_REPO_FILES:
                break

            path = os.path.join(root, filename)
            rel = os.path.relpath(path, repo_path).replace("\\", "/")

            if ext == ".py":
                parsed = _extract_python_ast(path)
                if parsed:
                    lines.append(
                        f"[PY] {rel} | imports={','.join(parsed['imports']) or '-'} | "
                        f"classes={','.join(parsed['classes']) or '-'} | "
                        f"funcs={','.join(parsed['functions']) or '-'}"
                    )
                else:
                    lines.append(f"[PY] {rel} | parse=failed")
            else:
                symbols = _extract_non_python_signatures(path)
                lines.append(f"[{ext[1:].upper()}] {rel} | symbols={','.join(symbols) or '-'}")

        if count > MAX_REPO_FILES:
            break

    summary = "\n".join(lines)[:MAX_REPO_SUMMARY_CHARS]
    return summary, count


def analyze_repository_path(repo_path: str, repo_url: str = ""):
    ast_summary, scanned = build_repo_ast_summary(repo_path)

    if not ast_summary.strip():
        return {
            "analysis": "No supported source files were found for AST-based analysis.",
            "type": "repo_empty",
        }

    if not GEMINI_API_KEY:
        return {
            "analysis": (
                "No Gemini API key was configured, so only structural scanning was completed.\n\n"
                f"Repository: {repo_url or 'N/A'}\n"
                f"Files analyzed: {scanned}"
            ),
            "type": "fallback",
        }

    prompt = SYSTEM_CONTEXT + f"""

Generate a repository README from this compact AST and symbol summary.

Requirements:
- Keep it concise and practical.
- Infer architecture from imports, classes, functions, and file structure.
- Include a meaningful Improvements & Future Work section.
- Do not invent implementation details you cannot support from the structure.

Repository: {repo_url or "N/A"}
Files analyzed: {scanned}

Structure:
{ast_summary}
"""

    result = call_gemini(prompt)

    if not result:
        return {
            "analysis": (
                "README generation failed.\n\n"
                f"Last Gemini error:\n{LAST_GEMINI_ERROR or 'Unknown error'}\n\n"
                "Structure preview:\n"
                f"{ast_summary[:1000]}"
            ),
            "type": "error",
        }

    return {
        "analysis": result,
        "type": "success",
        "scanned_files": scanned,
    }

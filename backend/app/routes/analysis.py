from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

import zipfile
import tempfile
import os
import subprocess
import requests

from app.services.ai_service import analyze_code, summarize_readme, analyze_repository_path
from app.services.analysis_service import save_analysis, get_user_analyses
from app.core.config import settings

router = APIRouter(tags=["analysis"])

security = HTTPBearer()

ALLOWED_EXTENSIONS = (".py", ".js", ".java", ".cpp")
IGNORE_FOLDERS = ("node_modules", ".git", "__pycache__")
MAX_FILES = 100


def github_repo_parts(repo_url: str):
    clean_url = repo_url.rstrip("/")
    parts = clean_url.replace("https://github.com/", "").replace("http://github.com/", "").split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")
    return parts[0], parts[1].replace(".git", "")


# 🔐 Token verification
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")


# 🔧 Shared function to read code
def extract_code_from_folder(base_path: str):
    full_code = ""
    file_count = 0

    for root, _, files in os.walk(base_path):

        # skip unwanted folders
        if any(ignored in root for ignored in IGNORE_FOLDERS):
            continue

        for file_name in files:
            if file_name.endswith(ALLOWED_EXTENSIONS):

                file_count += 1
                if file_count > MAX_FILES:
                    break

                file_path = os.path.join(root, file_name)

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        full_code += f"\n\n# FILE: {file_name}\n\n"
                        full_code += f.read()
                except:
                    continue

    return full_code


# 🔹 1. Analyze raw code
@router.post("/")
async def analyze(payload: dict, user=Depends(verify_token)):
    code = payload.get("code", "")
    email = user["sub"]

    if not code.strip():
        raise HTTPException(status_code=400, detail="Code is empty")

    result = analyze_code(code)
    await save_analysis(email, code, result)

    return result


# 🔹 2. Upload ZIP
@router.post("/upload")
async def analyze_repo(file: UploadFile = File(...), user=Depends(verify_token)):
    email = user["sub"]

    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Upload a ZIP file")

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, file.filename)

        with open(zip_path, "wb") as f:
            f.write(await file.read())

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)

        full_code = extract_code_from_folder(tmp_dir)

        if not full_code.strip():
            raise HTTPException(status_code=400, detail="No valid code files found")

        result = analyze_code(full_code)
        await save_analysis(email, full_code, result)

        return {
            "analysis": result
        }

# 🔹 3. GitHub repo
@router.post("/github")
async def analyze_github(payload: dict, user=Depends(verify_token)):
    repo_url = payload.get("repo_url")
    email = user["sub"]

    if not repo_url or "github.com" not in repo_url:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")

    try:
        repo_url = repo_url.rstrip("/")
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = os.path.join(tmp_dir, "repo")
            clone_result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, repo_dir],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if clone_result.returncode != 0:
                # Fallback to ZIP download if git clone fails.
                zip_url = repo_url + "/archive/refs/heads/main.zip"
                response = requests.get(zip_url, timeout=20)

                if response.status_code != 200:
                    zip_url = repo_url + "/archive/refs/heads/master.zip"
                    response = requests.get(zip_url, timeout=20)

                if response.status_code != 200:
                    raise Exception("Cannot clone or download repo")

                zip_path = os.path.join(tmp_dir, "repo.zip")
                with open(zip_path, "wb") as f:
                    f.write(response.content)

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(repo_dir)

                # GitHub zip extracts into a top-level folder. Use that folder if present.
                extracted = [
                    os.path.join(repo_dir, name)
                    for name in os.listdir(repo_dir)
                    if os.path.isdir(os.path.join(repo_dir, name))
                ]
                if extracted:
                    repo_dir = extracted[0]

            result = analyze_repository_path(repo_dir, repo_url)
            await save_analysis(email, f"repo:{repo_url}", result)

            return {
                "analysis": result
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🔹 4. History
@router.get("/history")
async def history(page: int = 1, limit: int = 5, user=Depends(verify_token)):
    email = user["sub"]
    return await get_user_analyses(email, page, limit)


# 🔹 5. Summarize repository README
async def _readme_summary_logic(payload: dict, email: str):
    repo_url = payload.get("repo_url")

    if not repo_url or "github.com" not in repo_url:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")

    owner, repo = github_repo_parts(repo_url)

    readme_names = ("README.md", "readme.md", "README", "README.rst")
    for branch in ("main", "master"):
        for readme_name in readme_names:
            readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{readme_name}"
            response = requests.get(readme_url, timeout=15)
            if response.status_code == 200 and response.text.strip():
                result = summarize_readme(response.text, repo_url)
                await save_analysis(email, f"readme:{repo_url}", result)
                return result

    raise HTTPException(status_code=404, detail="README not found on main or master branch")


@router.post("/github/readme-summary")
async def github_readme_summary(payload: dict, user=Depends(verify_token)):
    return await _readme_summary_logic(payload, user["sub"])


@router.post("/readme/intelligence")
async def readme_intelligence(payload: dict, user=Depends(verify_token)):
    return await _readme_summary_logic(payload, user["sub"])

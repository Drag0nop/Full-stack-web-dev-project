from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

import zipfile
import tempfile
import os
import requests

from app.services.ai_service import analyze_code
from app.services.analysis_service import save_analysis, get_user_analyses
from app.core.config import settings

router = APIRouter(tags=["analysis"])

security = HTTPBearer()

ALLOWED_EXTENSIONS = (".py", ".js", ".java", ".cpp")
IGNORE_FOLDERS = ("node_modules", ".git", "__pycache__")
MAX_FILES = 100


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

        zip_url = repo_url + "/archive/refs/heads/main.zip"
        response = requests.get(zip_url, timeout=15)

        if response.status_code != 200:
            zip_url = repo_url + "/archive/refs/heads/master.zip"
            response = requests.get(zip_url, timeout=15)

        if response.status_code != 200:
            raise Exception("Cannot download repo")

        with tempfile.TemporaryDirectory() as tmp_dir:
            zip_path = os.path.join(tmp_dir, "repo.zip")

            with open(zip_path, "wb") as f:
                f.write(response.content)

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

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 🔹 4. History
@router.get("/history")
async def history(limit: int = 10, user=Depends(verify_token)):
    email = user["sub"]
    return await get_user_analyses(email, limit)
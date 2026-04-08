import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .ai_service import DocumentationService
from .auth import authenticate_user, create_access_token, get_current_user, hash_password
from .config import get_settings
from .database import Base, engine, get_db
from .models import DocumentedFile, Project, User
from .repo_parser import parse_repository_from_zip, serialize_json
from .schemas import (
    ChatRequest,
    ChatResponse,
    FileDocRead,
    GithubImportRequest,
    ProjectDetail,
    ProjectSummary,
    Token,
    UserCreate,
    UserRead,
)

settings = get_settings()
Base.metadata.create_all(bind=engine)
docs_service = DocumentationService()

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_dir = Path(__file__).resolve().parents[2] / "frontend"
app.mount("/assets", StaticFiles(directory=frontend_dir / "assets"), name="assets")


@app.get("/")
def read_index():
    return RedirectResponse(url="/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/index.html")
def read_legacy_index():
    return RedirectResponse(url="/login", status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@app.get("/login")
def read_login():
    return FileResponse(frontend_dir / "login.html")


@app.get("/register")
def read_register():
    return FileResponse(frontend_dir / "register.html")


@app.get("/home")
def read_home():
    return FileResponse(frontend_dir / "home.html")


@app.post(f"{settings.api_prefix}/auth/register", response_model=UserRead)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post(f"{settings.api_prefix}/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return Token(access_token=create_access_token(user.email))


@app.get(f"{settings.api_prefix}/auth/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get(f"{settings.api_prefix}/projects", response_model=list[ProjectSummary])
def list_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(Project)
        .filter(Project.owner_id == current_user.id)
        .order_by(Project.created_at.desc())
        .all()
    )


@app.post(f"{settings.api_prefix}/projects/upload", response_model=ProjectDetail)
async def upload_project(
    name: str = Form(...),
    zip_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = await zip_file.read()
    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ZIP exceeds configured size limit")
    suffix = Path(zip_file.filename or "upload.zip").suffix or ".zip"
    with NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(content)
        temp_path = Path(temp_file.name)

    try:
        repo_data = parse_repository_from_zip(temp_path)
        generated_docs = docs_service.document_repository(repo_data)
    finally:
        temp_path.unlink(missing_ok=True)

    project = Project(
        name=name,
        source_type="zip",
        owner_id=current_user.id,
        tree_json=serialize_json(repo_data["tree"]),
        overview_markdown=generated_docs["overview_markdown"],
        metadata_json=serialize_json(repo_data["metadata"]),
    )
    db.add(project)
    db.flush()

    for file_entry in generated_docs["files"]:
        db.add(
            DocumentedFile(
                project_id=project.id,
                path=file_entry["path"],
                language=file_entry["language"],
                summary_markdown=file_entry["summary_markdown"],
                symbols_json=serialize_json(file_entry["symbols"]),
                content_preview=file_entry["content_preview"],
            )
        )

    db.commit()
    db.refresh(project)
    return _project_to_detail(project)


@app.post(f"{settings.api_prefix}/projects/import-github", response_model=ProjectDetail)
def import_github_project(
    payload: GithubImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owner, repo = _parse_github_repo(payload.repo_url)
    archive_url = _get_github_archive_url(owner, repo)
    repo_data = _download_and_parse_github_archive(archive_url)
    generated_docs = docs_service.document_repository(repo_data)

    project = Project(
        name=payload.name,
        source_type="github",
        owner_id=current_user.id,
        tree_json=serialize_json(repo_data["tree"]),
        overview_markdown=generated_docs["overview_markdown"],
        metadata_json=serialize_json({**repo_data["metadata"], "repo_url": payload.repo_url}),
    )
    db.add(project)
    db.flush()

    for file_entry in generated_docs["files"]:
        db.add(
            DocumentedFile(
                project_id=project.id,
                path=file_entry["path"],
                language=file_entry["language"],
                summary_markdown=file_entry["summary_markdown"],
                symbols_json=serialize_json(file_entry["symbols"]),
                content_preview=file_entry["content_preview"],
            )
        )

    db.commit()
    db.refresh(project)
    return _project_to_detail(project)


@app.get(f"{settings.api_prefix}/projects/{{project_id}}", response_model=ProjectDetail)
def get_project(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = _owned_project_or_404(project_id, current_user.id, db)
    return _project_to_detail(project)


@app.post(f"{settings.api_prefix}/projects/{{project_id}}/chat", response_model=ChatResponse)
def chat_with_project(
    project_id: int,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = _owned_project_or_404(project_id, current_user.id, db)
    project_payload = {
        "name": project.name,
        "overview_markdown": project.overview_markdown,
        "metadata": json.loads(project.metadata_json),
        "files": [
            {
                "path": file.path,
                "language": file.language,
                "summary_markdown": file.summary_markdown,
                "symbols": json.loads(file.symbols_json),
            }
            for file in project.files
        ],
    }
    answer = docs_service.answer_question(payload.question, project_payload)
    return ChatResponse(answer_markdown=answer)


def _owned_project_or_404(project_id: int, user_id: int, db: Session) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _parse_github_repo(repo_url: str) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(repo_url)
    if parsed.netloc not in {"github.com", "www.github.com"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only GitHub repository URLs are supported")

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub repository URL is incomplete")
    return path_parts[0], path_parts[1].removesuffix(".git")


def _get_github_archive_url(owner: str, repo: str) -> str:
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    request = urllib.request.Request(api_url, headers={"User-Agent": "autonomous-codebase-documenter"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GitHub repository not found") from exc
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Failed to inspect GitHub repository") from exc
    except urllib.error.URLError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to reach GitHub from the server") from exc

    default_branch = payload.get("default_branch")
    if not default_branch:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not determine the default branch")
    return f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{default_branch}"


def _download_and_parse_github_archive(archive_url: str) -> dict:
    request = urllib.request.Request(archive_url, headers={"User-Agent": "autonomous-codebase-documenter"})
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            content = response.read()
    except urllib.error.HTTPError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="GitHub archive download failed") from exc
    except urllib.error.URLError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to download the GitHub archive") from exc

    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Repository archive exceeds configured size limit")

    with NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
        temp_file.write(content)
        temp_path = Path(temp_file.name)

    try:
        return parse_repository_from_zip(temp_path)
    finally:
        temp_path.unlink(missing_ok=True)


def _project_to_detail(project: Project) -> ProjectDetail:
    return ProjectDetail(
        id=project.id,
        name=project.name,
        source_type=project.source_type,
        overview_markdown=project.overview_markdown,
        created_at=project.created_at,
        tree=json.loads(project.tree_json),
        metadata=json.loads(project.metadata_json),
        files=[
            FileDocRead(
                id=file.id,
                path=file.path,
                language=file.language,
                summary_markdown=file.summary_markdown,
                symbols=json.loads(file.symbols_json),
                content_preview=file.content_preview,
            )
            for file in sorted(project.files, key=lambda item: item.path.lower())
        ],
    )

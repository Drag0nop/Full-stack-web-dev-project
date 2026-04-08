from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserRead(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class FileDocRead(BaseModel):
    id: int
    path: str
    language: str
    summary_markdown: str
    symbols: list[dict[str, Any]]
    content_preview: str


class ProjectSummary(BaseModel):
    id: int
    name: str
    source_type: str
    overview_markdown: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectDetail(ProjectSummary):
    tree: dict[str, Any]
    metadata: dict[str, Any]
    files: list[FileDocRead]


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer_markdown: str


class GithubImportRequest(BaseModel):
    name: str
    repo_url: str

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False, default="zip")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tree_json = Column(Text, nullable=False)
    overview_markdown = Column(Text, nullable=False, default="")
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="projects")
    files = relationship("DocumentedFile", back_populates="project", cascade="all, delete-orphan")


class DocumentedFile(Base):
    __tablename__ = "documented_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    path = Column(String(1000), nullable=False)
    language = Column(String(50), nullable=False, default="text")
    summary_markdown = Column(Text, nullable=False, default="")
    symbols_json = Column(Text, nullable=False, default="[]")
    content_preview = Column(Text, nullable=False, default="")

    project = relationship("Project", back_populates="files")

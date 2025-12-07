from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from typing import Optional

from .db import Base


class Template(Base):
    __tablename__ = "templates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    tasks: Mapped[list["ExtractionTaskORM"]] = relationship(
        "ExtractionTaskORM", back_populates="template", cascade="all, delete-orphan"
    )


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(String(1024))
    file_type: Mapped[Optional[str]] = mapped_column(String(128))
    template_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("templates.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    template: Mapped[Optional["Template"]] = relationship("Template")
    tasks: Mapped[list["ExtractionTaskORM"]] = relationship(
        "ExtractionTaskORM", back_populates="project", cascade="all, delete-orphan"
    )
    results: Mapped[list["ExtractionResult"]] = relationship(
        "ExtractionResult", back_populates="project", cascade="all, delete-orphan"
    )


class ExtractionTaskORM(Base):
    __tablename__ = "extraction_tasks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    template_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("templates.id"), nullable=True)
    project_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("projects.id"), nullable=True)
    aim: Mapped[str] = mapped_column(Text, nullable=False)
    multi_row: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    template: Mapped[Optional["Template"]] = relationship("Template", back_populates="tasks")
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="tasks")
    fields: Mapped[list["SchemaFieldORM"]] = relationship(
        "SchemaFieldORM", back_populates="task", cascade="all, delete-orphan"
    )
    results: Mapped[list["ExtractionResult"]] = relationship(
        "ExtractionResult", back_populates="task", cascade="all, delete-orphan"
    )


class SchemaFieldORM(Base):
    __tablename__ = "schema_fields"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("extraction_tasks.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    task: Mapped["ExtractionTaskORM"] = relationship("ExtractionTaskORM", back_populates="fields")


class ExtractionResult(Base):
    __tablename__ = "extraction_results_json"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id"), nullable=False)
    task_id: Mapped[int] = mapped_column(Integer, ForeignKey("extraction_tasks.id"), nullable=False)
    data: Mapped[str] = mapped_column(Text, nullable=True)  # JSON string
    raw_extracted_json: Mapped[Optional[str]] = mapped_column(Text)  # optional raw json
    error: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="results")
    task: Mapped["ExtractionTaskORM"] = relationship("ExtractionTaskORM", back_populates="results")




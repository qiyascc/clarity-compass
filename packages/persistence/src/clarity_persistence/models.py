import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, ClassVar

from sqlalchemy import DateTime, Enum, ForeignKey, Index, LargeBinary, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(UTC)


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def finished(self) -> bool:
        return self in {RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED}


class Base(DeclarativeBase):
    type_annotation_map: ClassVar[dict[Any, Any]] = {
        dict[str, Any]: JSONB,
        datetime: DateTime(timezone=True),
    }


class Timestamped:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class Site(Timestamped, Base):
    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120))
    start_url: Mapped[str] = mapped_column(String(2048))
    profile: Mapped[dict[str, Any]]
    credentials: Mapped[bytes | None] = mapped_column(LargeBinary)
    extension_key_hash: Mapped[str | None] = mapped_column(String(128), unique=True)
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=utcnow)

    runs: Mapped[list["Run"]] = relationship(back_populates="site", cascade="all, delete-orphan")


class Run(Timestamped, Base):
    __tablename__ = "runs"
    __table_args__ = (Index("ix_runs_site_created", "site_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, name="run_status", values_callable=lambda e: [m.value for m in e]),
        default=RunStatus.QUEUED,
    )
    profile: Mapped[dict[str, Any]]
    stage: Mapped[str | None] = mapped_column(String(40))
    progress: Mapped[dict[str, Any]] = mapped_column(default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    report: Mapped[dict[str, Any] | None]
    started_at: Mapped[datetime | None]
    finished_at: Mapped[datetime | None]

    site: Mapped[Site] = relationship(back_populates="runs")
    pages: Mapped[list["PageRecord"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class PageRecord(Timestamped, Base):
    __tablename__ = "pages"
    __table_args__ = (Index("ix_pages_run_url", "run_id", "url"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"))
    url: Mapped[str] = mapped_column(String(2048))
    viewport: Mapped[str] = mapped_column(String(16))
    status_code: Mapped[int | None]
    title: Mapped[str] = mapped_column(String(512), default="")
    capture: Mapped[dict[str, Any]]
    predictions: Mapped[dict[str, Any] | None]
    review: Mapped[dict[str, Any] | None]

    run: Mapped[Run] = relationship(back_populates="pages")


class FindingRecord(Timestamped, Base):
    __tablename__ = "findings"
    __table_args__ = (Index("ix_findings_run_severity", "run_id", "severity"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"))
    page_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pages.id", ondelete="SET NULL"))
    category: Mapped[str] = mapped_column(String(32))
    severity: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16))
    data: Mapped[dict[str, Any]]

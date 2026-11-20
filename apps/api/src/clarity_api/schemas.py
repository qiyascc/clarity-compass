import json
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, SecretStr

from clarity_core.domain.prediction import PagePrediction
from clarity_core.domain.profile import AnalysisProfile
from clarity_persistence.models import PageRecord, Run, RunStatus, Site


class SiteIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    profile: AnalysisProfile


class SitePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    profile: AnalysisProfile | None = None


class SiteOut(BaseModel):
    id: uuid.UUID
    name: str
    start_url: str
    profile: AnalysisProfile
    has_credentials: bool
    has_extension_key: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def of(cls, site: Site) -> "SiteOut":
        return cls(
            id=site.id,
            name=site.name,
            start_url=site.start_url,
            profile=AnalysisProfile.model_validate(site.profile),
            has_credentials=site.credentials is not None,
            has_extension_key=site.extension_key_hash is not None,
            created_at=site.created_at,
            updated_at=site.updated_at,
        )


class LoginCredentials(BaseModel):
    login_url: str
    username: str = Field(min_length=1)
    password: SecretStr
    username_selector: str | None = None
    password_selector: str | None = None
    submit_selector: str | None = None

    def plaintext(self) -> bytes:
        data = self.model_dump(mode="json", exclude={"password"})
        return json.dumps({**data, "password": self.password.get_secret_value()}).encode()


class ExtensionKey(BaseModel):
    key: str


class RunOut(BaseModel):
    id: uuid.UUID
    site_id: uuid.UUID
    status: RunStatus
    stage: str | None
    progress: dict[str, Any]
    error: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None

    @classmethod
    def of(cls, run: Run) -> "RunOut":
        return cls.model_validate(run, from_attributes=True)


class PageOut(BaseModel):
    id: uuid.UUID
    url: str
    viewport: str
    status_code: int | None
    title: str
    capture: dict[str, Any]
    predictions: PagePrediction | None
    review: dict[str, Any] | None

    @classmethod
    def of(cls, page: PageRecord) -> "PageOut":
        return cls.model_validate(page, from_attributes=True)

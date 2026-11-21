from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from clarity_api.queue import RunQueue
from clarity_api.security import SessionSigner
from clarity_api.settings import Settings
from clarity_persistence.secrets import SecretBox

SESSION_COOKIE = "cc_session"


def settings(request: Request) -> Settings:
    value: Settings = request.app.state.settings
    return value


def signer(request: Request) -> SessionSigner:
    value: SessionSigner = request.app.state.signer
    return value


def secret_box(request: Request) -> SecretBox:
    value: SecretBox = request.app.state.secret_box
    return value


def run_queue(request: Request) -> RunQueue:
    value: RunQueue = request.app.state.queue
    return value


async def session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.sessions() as db:
        try:
            yield db
            await db.commit()
        except BaseException:
            await db.rollback()
            raise


def current_user(
    request: Request,
    signer: Annotated[SessionSigner, Depends(signer)],
    settings: Annotated[Settings, Depends(settings)],
) -> str:
    token = request.cookies.get(SESSION_COOKIE)
    username = signer.read(token) if token else None
    if username is None or settings.password_hash(username) is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not signed in")
    return username


Session = Annotated[AsyncSession, Depends(session)]
CurrentUser = Annotated[str, Depends(current_user)]
AppSettings = Annotated[Settings, Depends(settings)]
Signer = Annotated[SessionSigner, Depends(signer)]
Box = Annotated[SecretBox, Depends(secret_box)]
Queue = Annotated[RunQueue, Depends(run_queue)]

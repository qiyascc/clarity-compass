from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from clarity_api.queue import RunQueue
from clarity_api.routes import artifacts, auth, health, runs, sites
from clarity_api.security import LoginThrottle, SecretBox, SessionSigner
from clarity_api.settings import Settings
from clarity_persistence.database import create_engine, session_factory


def create_app(settings: Settings, queue: RunQueue) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(settings.database_url)
        app.state.sessions = session_factory(engine)
        async with queue.lifespan():
            yield
        await engine.dispose()

    app = FastAPI(title="Clarity Compass", lifespan=lifespan, docs_url="/api/docs")
    app.state.settings = settings
    app.state.queue = queue
    app.state.signer = SessionSigner(
        settings.secret_key.get_secret_value(), settings.session_max_age
    )
    app.state.secret_box = SecretBox(settings.credentials_key.get_secret_value())
    app.state.login_throttle = LoginThrottle()

    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    for module in (health, auth, sites, runs, artifacts):
        app.include_router(module.router, prefix="/api")
    return app

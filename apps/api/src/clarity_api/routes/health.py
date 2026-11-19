from fastapi import APIRouter
from sqlalchemy import text

from clarity_api.deps import Session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(db: Session) -> dict[str, str]:
    await db.execute(text("select 1"))
    return {"status": "ok"}

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from clarity_api.deps import AppSettings, CurrentUser

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


@router.get("/{key:path}")
async def artifact(key: str, settings: AppSettings, _: CurrentUser) -> FileResponse:
    root = settings.artifact_dir.resolve()
    path = (root / key).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "artifact not found")
    return FileResponse(path, headers={"Cache-Control": "private, max-age=86400"})

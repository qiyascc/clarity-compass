import uuid

from fastapi import APIRouter, HTTPException, Response, status

from clarity_api.deps import Box, CurrentUser, Session
from clarity_api.schemas import ExtensionKey, LoginCredentials, SiteIn, SiteOut, SitePatch
from clarity_api.security import hash_extension_key, new_extension_key
from clarity_persistence.models import Site
from clarity_persistence.repositories import SiteRepository

router = APIRouter(prefix="/sites", tags=["sites"])


async def load_site(db: Session, site_id: uuid.UUID) -> Site:
    site = await SiteRepository(db).get(site_id)
    if site is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "site not found")
    return site


@router.get("")
async def list_sites(db: Session, _: CurrentUser) -> list[SiteOut]:
    return [SiteOut.of(site) for site in await SiteRepository(db).list()]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_site(body: SiteIn, db: Session, _: CurrentUser) -> SiteOut:
    site = await SiteRepository(db).create(body.name, body.profile)
    await db.refresh(site)
    return SiteOut.of(site)


@router.get("/{site_id}")
async def get_site(site_id: uuid.UUID, db: Session, _: CurrentUser) -> SiteOut:
    return SiteOut.of(await load_site(db, site_id))


@router.patch("/{site_id}")
async def update_site(site_id: uuid.UUID, body: SitePatch, db: Session, _: CurrentUser) -> SiteOut:
    site = await load_site(db, site_id)
    await SiteRepository(db).update(site, name=body.name, profile=body.profile)
    await db.refresh(site)
    return SiteOut.of(site)


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_site(site_id: uuid.UUID, db: Session, _: CurrentUser) -> None:
    await SiteRepository(db).delete(await load_site(db, site_id))


@router.put("/{site_id}/credentials", status_code=status.HTTP_204_NO_CONTENT)
async def set_credentials(
    site_id: uuid.UUID, body: LoginCredentials, db: Session, box: Box, _: CurrentUser
) -> None:
    site = await load_site(db, site_id)
    site.credentials = body.to_login().seal(box)


@router.delete("/{site_id}/credentials", status_code=status.HTTP_204_NO_CONTENT)
async def clear_credentials(site_id: uuid.UUID, db: Session, _: CurrentUser) -> None:
    site = await load_site(db, site_id)
    site.credentials = None


@router.post("/{site_id}/extension-key", status_code=status.HTTP_201_CREATED)
async def rotate_extension_key(
    site_id: uuid.UUID, db: Session, response: Response, _: CurrentUser
) -> ExtensionKey:
    site = await load_site(db, site_id)
    key = new_extension_key()
    site.extension_key_hash = hash_extension_key(key)
    response.headers["Cache-Control"] = "no-store"
    return ExtensionKey(key=key)


@router.delete("/{site_id}/extension-key", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_extension_key(site_id: uuid.UUID, db: Session, _: CurrentUser) -> None:
    site = await load_site(db, site_id)
    site.extension_key_hash = None

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel

from clarity_api.deps import SESSION_COOKIE, AppSettings, CurrentUser, Signer
from clarity_api.security import LoginThrottle, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    username: str
    password: str


class Me(BaseModel):
    username: str


@router.post("/login", status_code=status.HTTP_204_NO_CONTENT)
async def login(
    body: Credentials, request: Request, response: Response, settings: AppSettings, signer: Signer
) -> None:
    throttle: LoginThrottle = request.app.state.login_throttle
    client = request.client.host if request.client else "unknown"
    if throttle.blocked(client):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "too many attempts")
    stored = settings.password_hash(body.username)
    # Unknown names still pay for a hash check so timing does not reveal which names exist.
    checked = verify_password(
        stored or settings.admin_password_hash.get_secret_value(), body.password
    )
    valid = stored is not None and checked
    if not valid:
        throttle.failed(client)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid credentials")
    throttle.reset(client)
    response.set_cookie(
        SESSION_COOKIE,
        signer.issue(body.username),
        max_age=settings.session_max_age,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        path="/",
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me")
async def me(user: CurrentUser) -> Me:
    return Me(username=user)

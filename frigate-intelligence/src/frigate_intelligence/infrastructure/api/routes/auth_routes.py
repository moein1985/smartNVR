import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel

from frigate_intelligence.domain.models.user_model import UserModel
from frigate_intelligence.infrastructure.auth.auth_service import AuthService
from frigate_intelligence.infrastructure.config.user_manager import UserManager

logger = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    role: str


class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    created_at: str
    is_seed: bool


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = "user"


class UpdateUserRequest(BaseModel):
    password: str | None = None
    role: str | None = None


def _get_auth_service() -> AuthService:
    return AuthService()


def _get_user_manager() -> UserManager:
    return UserManager()


def get_current_user_dependency(
    request: Request,
    auth: AuthService = Depends(_get_auth_service),
    user_manager: UserManager = Depends(_get_user_manager),
) -> UserModel:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header[7:]
    payload = auth.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload.get("sub")
    user = user_manager.get_by_id(user_id) if user_id else None
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def require_admin_dependency(
    user: UserModel = Depends(get_current_user_dependency),
) -> UserModel:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def create_auth_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

    @router.post("/login", response_model=LoginResponse)
    async def login(
        body: LoginRequest = Body(...),
        auth: AuthService = Depends(_get_auth_service),
        user_manager: UserManager = Depends(_get_user_manager),
    ):
        user = user_manager.get_by_username(body.username)
        if not user:
            logger.warning("[Auth] Login failed for user '%s': user not found", body.username)
            raise HTTPException(status_code=401, detail="Invalid username or password")
        if not auth.verify_password(body.password, user.password_hash):
            logger.warning(
                "[Auth] Login failed for user '%s': invalid password",
                body.username,
            )
            raise HTTPException(status_code=401, detail="Invalid username or password")
        token = auth.create_token(user.id, user.username, user.role)
        logger.info("[Auth] Login successful for user '%s'", body.username)
        return LoginResponse(
            token=token,
            username=user.username,
            role=user.role,
        )

    @router.get("/me", response_model=UserResponse)
    async def me(user: UserModel = Depends(get_current_user_dependency)):
        return UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            created_at=user.created_at,
            is_seed=user.is_seed,
        )

    @router.post("/logout")
    async def logout():
        return {"status": "ok", "message": "Logged out (client should discard token)"}

    return router


def create_user_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/users", tags=["users"])

    @router.get("", response_model=list[UserResponse])
    async def list_users(
        admin: UserModel = Depends(require_admin_dependency),
        user_manager: UserManager = Depends(_get_user_manager),
    ):
        users = user_manager.list_users()
        return [
            UserResponse(
                id=u.id,
                username=u.username,
                role=u.role,
                created_at=u.created_at,
                is_seed=u.is_seed,
            )
            for u in users
        ]

    @router.post("", response_model=UserResponse)
    async def create_user(
        body: CreateUserRequest = Body(...),
        admin: UserModel = Depends(require_admin_dependency),
        user_manager: UserManager = Depends(_get_user_manager),
    ):
        try:
            user = user_manager.create_user(
                username=body.username,
                password=body.password,
                role=body.role,
            )
        except ValueError as e:
            logger.warning("[UserManager] Create user failed: %s", e)
            raise HTTPException(status_code=400, detail=str(e)) from e
        return UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            created_at=user.created_at,
            is_seed=user.is_seed,
        )

    @router.put("/{user_id}", response_model=UserResponse)
    async def update_user(
        user_id: str,
        body: UpdateUserRequest = Body(...),
        admin: UserModel = Depends(require_admin_dependency),
        user_manager: UserManager = Depends(_get_user_manager),
    ):
        try:
            user = user_manager.update_user(
                user_id,
                password=body.password,
                role=body.role,
            )
        except ValueError as e:
            logger.warning("[UserManager] Update user failed: %s", e)
            raise HTTPException(status_code=400, detail=str(e)) from e
        return UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            created_at=user.created_at,
            is_seed=user.is_seed,
        )

    @router.delete("/{user_id}")
    async def delete_user(
        user_id: str,
        admin: UserModel = Depends(require_admin_dependency),
        user_manager: UserManager = Depends(_get_user_manager),
    ):
        try:
            user_manager.delete_user(user_id)
        except ValueError as e:
            logger.warning("[UserManager] Delete user failed: %s", e)
            raise HTTPException(status_code=400, detail=str(e)) from e
        return {"status": "ok", "message": "User deleted"}

    return router

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from frigate_intelligence.domain.models.user_model import UserModel

logger = logging.getLogger(__name__)

_SEED_USERS = [
    {
        "username": "admin",
        "password": "admin",
        "role": "admin",
        "is_seed": True,
    },
    {
        "username": "user",
        "password": "user",
        "role": "user",
        "is_seed": True,
    },
]


class UserManager:
    def __init__(self, file_path: str = "data/users.json") -> None:
        self._file_path = Path(file_path)
        self._users: list[UserModel] = []
        self._load()

    def _load(self) -> None:
        if not self._file_path.exists():
            logger.info(
                "[UserManager] Users file not found at %s, seeding defaults",
                self._file_path,
            )
            self._seed_defaults()
            return
        try:
            raw = self._file_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            self._users = [UserModel(**u) for u in data.get("users", [])]
            logger.info(
                "[UserManager] Loaded %d users from %s",
                len(self._users),
                self._file_path,
            )
        except Exception as e:
            logger.error(
                "[UserManager] Failed to load users from %s: %s",
                self._file_path,
                e,
                exc_info=True,
            )
            self._seed_defaults()

    def _seed_defaults(self) -> None:
        from frigate_intelligence.infrastructure.auth.auth_service import AuthService

        auth = AuthService()
        self._users = []
        for seed in _SEED_USERS:
            user = UserModel(
                id=uuid.uuid4().hex,
                username=seed["username"],
                password_hash=auth.hash_password(seed["password"]),
                role=seed["role"],
                created_at=datetime.now(timezone.utc).isoformat(),
                is_seed=seed["is_seed"],
            )
            self._users.append(user)
        self._save()
        logger.info(
            "[UserManager] Seeded %d default users (admin, user)",
            len(self._users),
        )

    def _save(self) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"users": [u.model_dump() for u in self._users]}
        raw = json.dumps(data, indent=2, ensure_ascii=False)
        self._file_path.write_text(raw, encoding="utf-8")
        logger.info("[UserManager] Saved %d users to %s", len(self._users), self._file_path)

    def list_users(self) -> list[UserModel]:
        return list(self._users)

    def get_by_username(self, username: str) -> UserModel | None:
        for u in self._users:
            if u.username == username:
                return u
        return None

    def get_by_id(self, user_id: str) -> UserModel | None:
        for u in self._users:
            if u.id == user_id:
                return u
        return None

    def create_user(
        self,
        username: str,
        password: str,
        role: str = "user",
    ) -> UserModel:
        from frigate_intelligence.infrastructure.auth.auth_service import AuthService

        if self.get_by_username(username):
            raise ValueError(f"Username '{username}' already exists")
        if role not in ("admin", "user"):
            raise ValueError(f"Invalid role '{role}', must be 'admin' or 'user'")

        auth = AuthService()
        user = UserModel(
            id=uuid.uuid4().hex,
            username=username,
            password_hash=auth.hash_password(password),
            role=role,
            created_at=datetime.now(timezone.utc).isoformat(),
            is_seed=False,
        )
        self._users.append(user)
        self._save()
        logger.info("[UserManager] Created user '%s' with role '%s'", username, role)
        return user

    def update_user(
        self,
        user_id: str,
        password: str | None = None,
        role: str | None = None,
    ) -> UserModel:
        user = self.get_by_id(user_id)
        if not user:
            raise ValueError(f"User '{user_id}' not found")

        from frigate_intelligence.infrastructure.auth.auth_service import AuthService

        if password:
            auth = AuthService()
            user.password_hash = auth.hash_password(password)
            logger.info("[UserManager] Updated password for user '%s'", user.username)
        if role:
            if role not in ("admin", "user"):
                raise ValueError(f"Invalid role '{role}', must be 'admin' or 'user'")
            user.role = role
            logger.info(
                "[UserManager] Updated role for user '%s' to '%s'",
                user.username,
                role,
            )
        self._save()
        return user

    def delete_user(self, user_id: str) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            raise ValueError(f"User '{user_id}' not found")
        if user.is_seed:
            raise ValueError("Seed users cannot be deleted")
        self._users.remove(user)
        self._save()
        logger.info("[UserManager] Deleted user '%s'", user.username)
        return True

from pydantic import BaseModel


class UserModel(BaseModel):
    id: str
    username: str
    password_hash: str
    role: str = "user"
    created_at: str = ""
    is_seed: bool = False

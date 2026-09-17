import re

from pydantic import BaseModel

_PASSWORD_MIN_LENGTH = 8


def validate_password_strength(password: str) -> str:
    if len(password) < _PASSWORD_MIN_LENGTH:
        raise ValueError(f"Password must be at least {_PASSWORD_MIN_LENGTH} characters long.")
    if not re.search(r"[A-Za-z]", password):
        raise ValueError("Password must contain at least one letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    return password


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class MessageResponse(BaseModel):
    message: str

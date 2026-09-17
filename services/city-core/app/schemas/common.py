from pydantic import BaseModel


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class MessageResponse(BaseModel):
    message: str

from pydantic import BaseModel
from datetime import datetime
from typing import Generic, TypeVar, List

T = TypeVar("T")


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    error: str


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

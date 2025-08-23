from typing import Generic, List, TypeVar
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")

class PaginationMeta(BaseModel):
    current_page: int
    per_page: int
    total: int
    last_page: int

class PaginatedResponse(GenericModel, Generic[T]):
    data: List[T]
    pagination: PaginationMeta

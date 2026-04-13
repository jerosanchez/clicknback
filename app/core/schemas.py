from pydantic import BaseModel


class PaginationOut(BaseModel):
    offset: int
    limit: int
    total: int

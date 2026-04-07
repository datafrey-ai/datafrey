from datetime import datetime

from pydantic import BaseModel


class IndexStatus(BaseModel):
    indexed_at: datetime | None
    column_count: int
    table_count: int

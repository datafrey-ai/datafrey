from datetime import datetime

from pydantic import BaseModel


class IndexStatus(BaseModel):
    indexed_at: datetime | None
    column_count: int
    table_count: int
    is_indexing: bool = False
    tables_done: int | None = None
    tables_total: int | None = None
    current_table: str | None = None

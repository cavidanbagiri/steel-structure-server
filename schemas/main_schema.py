from pydantic import BaseModel
from typing import Optional

class InsertTransportSchema(BaseModel):
    row_id: int                              # ID of the main table row
    qty: int
    status: Optional[str] = None
    order_no: Optional[str] = None
    area: Optional[str] = None
    location: Optional[str] = None
    created_by: Optional[int] = None        # User ID from frontend
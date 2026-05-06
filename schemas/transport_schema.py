from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional

class TransportBase(BaseModel):
    structure_1: Optional[str] = None
    structure_2: Optional[str] = None
    raw_labels: Optional[str] = None
    mark_name: Optional[str] = None
    t_qty: Optional[float] = None
    t_weight: Optional[float] = None
    t_date: Optional[date] = None
    t_status: Optional[str] = None
    proce_qty: Optional[int] = None
    order_no: Optional[str] = None
    key: Optional[str] = None
    area: Optional[str] = None
    location: Optional[str] = None

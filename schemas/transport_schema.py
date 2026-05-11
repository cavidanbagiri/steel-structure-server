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


class InsertErectedSchema(BaseModel):
    transport_id: int                         # ID from transport table
    e_qty: int                                # Erected quantity (can't exceed transport.t_qty)
    altitude_mark_1: Optional[str] = None
    altitude_mark_2: Optional[str] = None
    axis: Optional[str] = None
    range: Optional[str] = None
    created_by: int
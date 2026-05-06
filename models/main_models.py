
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.base import Base

from models.user_model import UserModel

class TransportModel(Base):
    __tablename__ = "transports"

    id = Column(Integer, primary_key=True, index=True)
    structure_1 = Column(String, nullable=True)
    structure_2 = Column(String, nullable=True)
    raw_labels = Column(String, nullable=True)
    mark_name = Column(String, nullable=True)
    t_qty = Column(Float, nullable=True)
    t_weight = Column(Float, nullable=True)
    t_date = Column(Date, nullable=True)
    t_status = Column(String, nullable=True)
    proce_qty = Column(Integer, nullable=True)
    order_no = Column(String, nullable=True)
    key = Column(String, nullable=True)
    area = Column(String, nullable=True)
    location = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    creator = relationship("UserModel", back_populates="transports")

    def __repr__(self):
        return f"<Transport {self.id} - {self.mark_name}>"
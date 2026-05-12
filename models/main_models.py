
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
    t_leftover_qty = Column(Float, nullable=True)
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
    combines = relationship("Combine", back_populates="transport")

    def __repr__(self):
        return f"<Transport {self.id} - {self.mark_name}>"


class Mains(Base):
    __tablename__ = "mains"

    id = Column(Integer, primary_key=True, index=True)
    area = Column(String, nullable=True)
    zone = Column(String, nullable=True)
    key = Column(String, nullable=True)
    row_labels = Column(String, nullable=True)
    item = Column(String, nullable=True)
    p_s = Column(String, nullable=True)  # p/s field
    qty = Column(Float, nullable=True)
    left_over_qty = Column(Float, nullable=True)  # NEW: Remaining quantity
    description = Column(String, nullable=True)
    section = Column(String, nullable=True)
    length = Column(Float, nullable=True)
    weight = Column(Float, nullable=True)
    weight_total = Column(Float, nullable=True)
    dwgn = Column(String, nullable=True)

    combines = relationship("Combine", back_populates="main")


class Erected(Base):
    __tablename__ = "erecteds"

    id = Column(Integer, primary_key=True, index=True)
    area = Column(String, nullable=True)
    structure = Column(String, nullable=True)
    row_labels = Column(String, nullable=True)
    mark_names = Column(String, nullable=True)
    e_qty = Column(Float, nullable=True)
    e_weight = Column(Float, nullable=True)  # e-weight field
    daily_e_date = Column(Date, nullable=True)
    proce_qty = Column(Float, nullable=True)
    altitude_mark_1 = Column(String, nullable=True)
    axis = Column(String, nullable=True)
    range = Column(String, nullable=True)
    altitude_mark_2 = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    creator = relationship("UserModel", back_populates="erecteds")
    combines = relationship("Combine", back_populates="erected")


class Combine(Base):
    __tablename__ = "combine"

    id = Column(Integer, primary_key=True, index=True)
    transport_id = Column(Integer, ForeignKey("transports.id", ondelete="SET NULL"), nullable=True)
    main_id = Column(Integer, ForeignKey("mains.id", ondelete="SET NULL"), nullable=True)
    erected_id = Column(Integer, ForeignKey("erecteds.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    transport = relationship("TransportModel", back_populates="combines")
    main = relationship("Mains", back_populates="combines")
    erected = relationship("Erected", back_populates="combines")
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Enum, ForeignKey, Numeric, String, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Column
from geoalchemy2 import Geometry

from app.models import Base


class VolunteerSchedule(Base):
    __tablename__ = "volunteer_schedules"
    __table_args__ = (
        Index("ix_volunteer_schedules_volunteer_id", "volunteer_id"),
        Index("ix_volunteer_schedules_available_date_status", "available_date", "status"),
        Index("ix_volunteer_schedules_route", "route", postgresql_using="gist"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    volunteer_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    post_id = Column(BigInteger, ForeignKey("transport_posts.id"), nullable=True)
    route_description = Column(Text, nullable=False)
    route = Column(Geometry("LINESTRING", srid=4326, spatial_index=False), nullable=True)
    available_date = Column(Date, nullable=False)
    available_time = Column(String(5), nullable=True)
    origin_area = Column(String(100), nullable=False)
    destination_area = Column(String(100), nullable=False)
    vehicle_available = Column(Boolean, nullable=False)
    max_animal_size = Column(
        Enum("small", "medium", "large", name="animal_size_schedule_enum"),
        nullable=False,
    )
    status = Column(
        Enum("available", "matched", "expired", name="schedule_status_enum"),
        nullable=False,
        default="available",
        server_default="available",
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    volunteer = relationship("User", back_populates="volunteer_schedules")
    post = relationship("TransportPost", back_populates="volunteer_schedules")


class VolunteerHistory(Base):
    __tablename__ = "volunteer_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    volunteer_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    segment_id = Column(BigInteger, ForeignKey("relay_segments.id"), unique=True, nullable=False)
    distance_km = Column(Numeric(6, 2), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=False)

    volunteer = relationship("User", back_populates="volunteer_history")
    segment = relationship("RelaySegment", back_populates="volunteer_history")

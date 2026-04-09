from sqlalchemy import BigInteger, String, Enum, DateTime, Date, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Column
import uuid

from app.models import Base


class TransportPost(Base):
    __tablename__ = "transport_posts"
    __table_args__ = (
        Index("ix_transport_posts_status_scheduled_date", "status", "scheduled_date"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    shelter_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    status = Column(
        Enum("recruiting", "in_transit", "completed", "cancelled", name="post_status_enum"),
        nullable=False,
        default="recruiting",
        server_default="recruiting",
    )
    animal_name = Column(String(50), nullable=False)
    animal_size = Column(
        Enum("small", "medium", "large", name="animal_size_post_enum"),
        nullable=False,
    )
    animal_photo_url = Column(String(500), nullable=True)
    animal_notes = Column(Text, nullable=True)
    origin = Column(String(255), nullable=False)
    destination = Column(String(255), nullable=False)
    scheduled_date = Column(Date, nullable=False)
    share_token = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    shelter = relationship("User", back_populates="transport_posts")
    volunteer_schedules = relationship("VolunteerSchedule", back_populates="post")
    relay_chains = relationship("RelayChain", back_populates="transport_post")
    notifications = relationship("Notification", back_populates="transport_post")

from sqlalchemy import BigInteger, SmallInteger, String, Text, Enum, DateTime, Numeric, ForeignKey, CHAR, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Column

from app.models import Base


class RelayChain(Base):
    __tablename__ = "relay_chains"
    __table_args__ = (
        Index("ix_relay_chains_transport_post_id", "transport_post_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    transport_post_id = Column(BigInteger, ForeignKey("transport_posts.id"), nullable=False)
    backup_candidates = Column(JSONB, nullable=True)
    matching_reason = Column(Text, nullable=True)
    status = Column(
        Enum("proposed", "active", "completed", "broken", name="chain_status_enum"),
        nullable=False,
        default="proposed",
        server_default="proposed",
    )
    chain_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    transport_post = relationship("TransportPost", back_populates="relay_chains")
    segments = relationship("RelaySegment", back_populates="chain")


class RelaySegment(Base):
    __tablename__ = "relay_segments"
    __table_args__ = (
        Index("ix_relay_segments_chain_id", "chain_id"),
        Index("ix_relay_segments_volunteer_id_status", "volunteer_id", "status"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    chain_id = Column(BigInteger, ForeignKey("relay_chains.id"), nullable=False)
    volunteer_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    segment_order = Column(SmallInteger, nullable=False)
    pickup_location = Column(String(255), nullable=False)
    dropoff_location = Column(String(255), nullable=False)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    estimated_arrival = Column(DateTime(timezone=True), nullable=True)
    handover_code = Column(CHAR(6), nullable=True)
    handover_code_given_at = Column(DateTime(timezone=True), nullable=True)
    handover_code_received_at = Column(DateTime(timezone=True), nullable=True)
    handover_method = Column(
        Enum("code", "manual_approval", name="handover_method_enum"),
        nullable=True,
    )
    ping_sent_at = Column(DateTime(timezone=True), nullable=True)
    ping_responded_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        Enum(
            "pending", "accepted", "in_progress", "completed",
            "needs_verification", "no_show",
            name="segment_status_enum",
        ),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    declined_at = Column(DateTime(timezone=True), nullable=True)
    decline_reason = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    chain = relationship("RelayChain", back_populates="segments")
    volunteer = relationship("User", back_populates="relay_segments")
    checkpoints = relationship("Checkpoint", back_populates="segment")
    volunteer_history = relationship("VolunteerHistory", back_populates="segment", uselist=False)


class Checkpoint(Base):
    __tablename__ = "checkpoints"
    __table_args__ = (
        Index("ix_checkpoints_segment_id", "segment_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    segment_id = Column(BigInteger, ForeignKey("relay_segments.id"), nullable=False)
    type = Column(
        Enum("departure", "waypoint", "arrival", name="checkpoint_type_enum"),
        nullable=False,
    )
    latitude = Column(Numeric(9, 6), nullable=True)
    longitude = Column(Numeric(9, 6), nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    segment = relationship("RelaySegment", back_populates="checkpoints")

from sqlalchemy import BigInteger, String, SmallInteger, Text, Enum, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Column

from app.models import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    transport_post_id = Column(BigInteger, ForeignKey("transport_posts.id"), nullable=True)
    type = Column(String(50), nullable=False)
    channel = Column(
        Enum("in_app", "email", "push", name="notification_channel_enum"),
        nullable=False,
    )
    payload = Column(JSONB, nullable=False)
    status = Column(
        Enum("pending", "sent", "failed", name="notification_status_enum"),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    retry_count = Column(SmallInteger, nullable=False, default=0, server_default="0")
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="notifications")
    transport_post = relationship("TransportPost", back_populates="notifications")


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    __table_args__ = (
        UniqueConstraint("user_id", "endpoint", name="uq_push_subscriptions_user_endpoint"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    endpoint = Column(Text, nullable=False)
    p256dh = Column(Text, nullable=False)
    auth = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="push_subscriptions")

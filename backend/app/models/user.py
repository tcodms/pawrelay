from sqlalchemy import BigInteger, String, Enum, DateTime, Boolean, ARRAY, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Column

from app.models import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(Enum("shelter", "volunteer", "admin", name="user_role"), nullable=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    account_status = Column(
        Enum("active", "suspended", "banned", name="account_status_enum"),
        nullable=False,
        default="active",
        server_default="active",
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    shelter_profile = relationship("ShelterProfile", back_populates="user", uselist=False)
    volunteer_profile = relationship("VolunteerProfile", back_populates="user", uselist=False)
    transport_posts = relationship("TransportPost", back_populates="shelter")
    volunteer_schedules = relationship("VolunteerSchedule", back_populates="volunteer")
    relay_segments = relationship("RelaySegment", back_populates="volunteer")
    notifications = relationship("Notification", back_populates="user")
    volunteer_history = relationship("VolunteerHistory", back_populates="volunteer")
    push_subscriptions = relationship("PushSubscription", back_populates="user")


class ShelterProfile(Base):
    __tablename__ = "shelter_profiles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    shelter_registration_doc_url = Column(String(500), nullable=True)
    verification_notes = Column(String, nullable=True)
    operating_hours = Column(String(100), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="shelter_profile")


class VolunteerProfile(Base):
    __tablename__ = "volunteer_profiles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, unique=True)
    vehicle_available = Column(Boolean, nullable=False, default=False, server_default="false")
    max_animal_size = Column(
        Enum("small", "medium", "large", name="animal_size_enum"),
        nullable=False,
    )
    activity_regions = Column(ARRAY(String(50)), nullable=False)

    user = relationship("User", back_populates="volunteer_profile")

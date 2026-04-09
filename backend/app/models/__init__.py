from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.user import User, ShelterProfile, VolunteerProfile  # noqa: E402, F401
from app.models.post import TransportPost  # noqa: E402, F401
from app.models.volunteer import VolunteerSchedule, VolunteerHistory  # noqa: E402, F401
from app.models.relay import RelayChain, RelaySegment, Checkpoint  # noqa: E402, F401
from app.models.waypoint import Waypoint  # noqa: E402, F401
from app.models.notification import Notification, PushSubscription  # noqa: E402, F401

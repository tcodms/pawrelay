from sqlalchemy import BigInteger, String, Enum
from sqlalchemy.orm import relationship
from sqlalchemy import Column
from geoalchemy2 import Geometry

from app.models import Base


class Waypoint(Base):
    __tablename__ = "waypoints"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    type = Column(
        Enum("rest_area", "train", "bus", "shelter", name="waypoint_type_enum"),
        nullable=False,
    )
    address = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    source = Column(String(50), nullable=False)

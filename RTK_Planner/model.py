from ast import Pass
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Table, create_engine, engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import enum


class Status(enum.Enum):
    unknown = 0
    active = enum.auto()
    inactive = enum.auto()


db_url = "sqlite:///rover.db"

engine = create_engine(db_url)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()


class RoverTrail(Base):
    __tablename__ = "rover_trial"
    id = Column(Integer, primary_key=True)
    rover_id = Column("rover_id", Integer, ForeignKey("rovers.id"))
    trail_id = Column("trail_id", Integer, ForeignKey("trails.id"))


class Rover(Base):
    __tablename__ = "rovers"
    id = Column(Integer, primary_key=True)
    mac = Column(String, unique=True, nullable=False)
    name = Column(String, unique=True, nullable=False)
    status = Column(Integer, default=Status.unknown.value)
    last_active = Column(DateTime, default=datetime.utcnow)
    trails = relationship("Trail", secondary="rover_trial", back_populates="rovers")


class Trail(Base):
    __tablename__ = "trails"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    trail_points = Column(String, unique=True, nullable=False)
    rovers = relationship("Rover", secondary="rover_trial", back_populates="trails")


# Test it

Base.metadata.create_all(engine)

#rover2 = Rover(mac="2", name="Rover2")
#rover1 = Rover(mac="1", name="Rover1")
#trail1 = Trail(trail_points="1.2,3.3;1.2,3.4", rovers=[rover1])
#trail2 = Trail(trail_points="1.2,3.3;1.2,3.4;1.2,3.5", rovers=[rover1, rover2])

#session.add_all([rover1, rover2, trail1, trail2])
#session.commit()


def new_rover(rover_mac: str, rover_name: str) -> None:
    is_rover = session.query(Rover).filter_by(name=rover_name).first()
    if is_rover:
        print(f"Rover name: {rover_name} exists.")
        return
    rover = Rover(mac=rover_mac, name=rover_name)
    session.add_all([rover])
    session.commit()

def new_rover_with_existing_trails(rover_mac: str, rover_name: str, trail_id: int) -> None:
    trail = session.query(Trail).filter_by(id=trail_id).first()
    rover = Rover(mac=rover_mac, name=rover_name, trails=[trail])
    session.add_all([rover])
    session.commit()

def existing_rover_existing_trials(rover_name: str, trail_name: str) -> None:
    rover_id = session.query(Rover.id).filter_by(name=rover_name).first()
    trail_id = session.query(Trail.id).filter_by(name=trail_name).first()
    if not rover_id:
        print(f"Cannot update. Rover {rover_name} does not exist.")
        return
    if not trail_id:
        print(f"Cannot update. Trail ID {trial_id_to_set} does not exist.")
        return

    rover_trial = RoverTrail(rover_id = rover_id[0], trail_id = trail_id[0])
    session.add_all([rover_trial])
    session.commit()

def get_rover_trials(rover_name: str) -> list:
    rover = session.query(Rover).filter_by(name=rover_name).first()
    trails = [trail.trail_points for trail in rover.trails]
    print(trails)
    return trails


#new_rover_with_existing_trails("123", "Rover3", 1)
new_rover("1", "Rover1")
new_rover("2", "Rover2")
new_rover("3", "Rover3")
#existing_rover_existing_trials("Rover5", 1)
get_rover_trials("Rover2")
get_rover_trials("Rover1")
get_rover_trials("Rover3")



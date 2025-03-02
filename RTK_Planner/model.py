from ast import Pass
# from sqlalchemy import Column, ForeignKey, Integer, String, DateTime, Table, create_engine, engine
# from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import enum
from config import sqla, mars, app


class Status(enum.Enum):
    unknown = 0
    active = enum.auto()
    inactive = enum.auto()


class RoverTrail(sqla.Model):
    __tablename__ = "RoverTrial"
    id = sqla.Column(sqla.Integer, primary_key=True)
    rover_id = sqla.Column("rover_id", sqla.Integer, sqla.ForeignKey("Rover.id"))
    trail_id = sqla.Column("trail_id", sqla.Integer, sqla.ForeignKey("Trail.id"))


class RoverTrailSchema(mars.SQLAlchemyAutoSchema):
    class Meta:
        model = RoverTrail
        load_instance = True
        sqla_session = sqla.session
        include_fk = True


rovertrail_schema = RoverTrailSchema()


class Rover(sqla.Model):
    __tablename__ = "Rover"
    id = sqla.Column(sqla.Integer, primary_key=True)
    mac = sqla.Column(sqla.String, unique=True, nullable=False)
    name = sqla.Column(sqla.String, unique=True, nullable=False)
    status = sqla.Column(sqla.Integer, default=Status.unknown.value)
    last_active = sqla.Column(sqla.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    trails = sqla.relationship("Trail", secondary="RoverTrial", back_populates="Rover")


class RoverSchema(mars.SQLAlchemyAutoSchema):
    class Meta:
        model = Rover
        load_instance = True
        sqla_session = sqla.session
        include_relationships = True


rover_schema = RoverSchema()


class Trail(sqla.Model):
    __tablename__ = "Trail"
    id = sqla.Column(sqla.Integer, primary_key=True)
    name = sqla.Column(sqla.String, unique=True, nullable=False)
    trail_points = sqla.Column(sqla.String, unique=True, nullable=False)
    rovers = sqla.relationship("Rover", secondary="RoverTrial", back_populates="Trail")


class TrailSchema(mars.SQLAlchemyAutoSchema):
    class Meta:
        model = Trail
        load_instance = True
        sqla_session = sqla.session
        include_relationships = True


trail_schema = TrailSchema()


if __name__ == "__main__":
    # Test it
    engine = sqla.create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
    Session = sqla.sessionmaker(bind=engine)
    session = Session()

    sqla.Base.metadata.create_all(engine)

    rover2 = Rover(mac="2", name="Rover2")
    rover1 = Rover(mac="1", name="Rover1")
    trail1 = Trail(trail_points="1.2,3.3;1.2,3.4", rovers=[rover1])
    trail2 = Trail(trail_points="1.2,3.3;1.2,3.4;1.2,3.5", rovers=[rover1, rover2])
    session.add_all([rover1, rover2, trail1, trail2])
    session.commit()


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
            print(f"Cannot update. Trail ID {rover_id} does not exist.")
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



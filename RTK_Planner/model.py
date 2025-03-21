from ast import Pass
from datetime import datetime
import enum
from config import sqla, mars, app


class Status(enum.Enum):
    unknown = 0
    active = enum.auto()
    inactive = enum.auto()


class RoverTrail(sqla.Model):
    __tablename__ = 'rover_trail'
    rover_id = sqla.Column(sqla.Integer, sqla.ForeignKey('rover.id'), primary_key=True)
    trail_id = sqla.Column(sqla.Integer, sqla.ForeignKey('trail.id'), primary_key=True)

    def __init__(self, rover_id, trail_id):
        self.rover_id = rover_id
        self.trail_id = trail_id


class Rover(sqla.Model):
    __tablename__ = 'rover'
    id = sqla.Column(sqla.Integer, primary_key=True)
    mac = sqla.Column(sqla.String, unique=True, nullable=False)
    name = sqla.Column(sqla.String, unique=True, nullable=False)
    status = sqla.Column(sqla.Integer, default=Status.unknown.value)
    last_active = sqla.Column(sqla.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    trails = sqla.relationship('Trail', secondary='rover_trail', backref=sqla.backref('rovers', lazy='dynamic'))

    def __init__(self, name, mac, status, last_active, trails):
        self.name = name
        self.mac = mac
        self.status = status
        self.last_active = last_active
        self.trails = trails


class Trail(sqla.Model):
    __tablename__ = 'trail'
    id = sqla.Column(sqla.Integer, primary_key=True)
    name = sqla.Column(sqla.String(100), nullable=False)
    trail_points = sqla.Column(sqla.String, unique=True, nullable=False)

    def __init__(self, name, trail_points):
        self.name = name
        self.trail_points = trail_points


class RoverSchema(mars.Schema):
    class Meta:
        fields = ('id', 'name', "mac", "status", "last_active")


class TrailSchema(mars.Schema):
    class Meta:
        fields = ('id', 'name', "trail_points")


class RoverWithTrailsSchema(mars.Schema):
    class Meta:
        fields = ('id', 'name', 'trails')
    trails = mars.Nested(TrailSchema, many=True)


class TrailWithRoversSchema(mars.Schema):
    class Meta:
        fields = ('id', 'name', 'rovers')
    rovers = mars.Nested(RoverSchema, many=True)


# Initialize schemas
rover_schema = RoverSchema()
rovers_schema = RoverSchema(many=True)
trail_schema = TrailSchema()
trails_schema = TrailSchema(many=True)
rover_with_trails_schema = RoverWithTrailsSchema()
trail_with_rovers_schema = TrailWithRoversSchema()


if __name__ == "__main__":
    # Test it
    engine = sqla.create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
    Session = sqla.sessionmaker(bind=engine)
    session = Session()

    sqla.metadata.create_all(engine)

    #sqla.Base.metadata.create_all(engine)

    trail1 = Trail(name="a", trail_points="1.2,3.3;1.2,3.4")
    trail2 = Trail(name="b", trail_points="1.2,3.3;1.2,3.4;1.2,3.5")
    rover1 = Rover(mac="a8032a56ae8d", name="Rover1", status=1, last_active=datetime.today(), trails=[trail1])
    rover2 = Rover(mac="21", name="Rover2", status=1, last_active=datetime.today(), trails=[trail2, trail1])
    rover2 = Rover(mac="a8032a56ae8c", name="Rover3", status=1, last_active=datetime.today(), trails=[trail2, trail1])
    session.add_all([rover1, rover2, trail1, trail2])
    session.commit()

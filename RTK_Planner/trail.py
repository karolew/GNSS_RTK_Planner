from flask import abort, make_response, request, jsonify
from model import RoverTrail, Rover, rover_with_trails_schema, rovers_schema, trail_with_rovers_schema, rover_schema, Trail, TrailSchema, trails_schema
from config import sqla
import json
from datetime import datetime


def get_all():
    _trails = Trail.query.all()
    return trails_schema.dump(_trails)


def get_trails_by_rover(rover_id):
    rover = Rover.query.filter(Rover.id == rover_id).one_or_none()
    return trails_schema.dump(rover.trails)

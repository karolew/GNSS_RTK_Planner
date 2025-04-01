from flask import abort, make_response, request, jsonify
from model import RoverTrail, Rover, rover_with_trails_schema, rovers_schema, trail_with_rovers_schema, rover_schema, Trail, TrailSchema, trails_schema, trail_schema
from config import sqla
import json
from datetime import datetime


def get_all():
    _trails = Trail.query.all()
    return trails_schema.dump(_trails)

def create_trail():
    data = request.get_json()
    if Trail.query.filter(Trail.name == data['name']).first() is not None:
        return {"error": "Trail already exists"}, 400

    new_trail = Trail(
        name=data["name"],
        trail_points = str(data["trail_points"])    # Whole list to string.
    )

    sqla.session.add(new_trail)
    sqla.session.commit()

    return trail_schema.dump(new_trail)


def get_trails_by_rover(rover_id):
    rover = Rover.query.filter(Rover.id == rover_id).one_or_none()
    return trails_schema.dump(rover.trails)

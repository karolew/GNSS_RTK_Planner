from flask import abort, make_response, request, jsonify
from model import RoverTrail, Rover, rover_with_trails_schema, rovers_schema, trail_with_rovers_schema, rover_schema, Trail, TrailSchema
from config import sqla
import json
from datetime import datetime


def get_trails_by_rover(rover_id):
    rover = Rover.query.get_or_404(rover_id)
    trails = rover.trails
    trail_schema = TrailSchema(many=True)
    return trail_schema.dump(trails)

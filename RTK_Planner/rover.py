from flask import abort, make_response
from model import RoverTrail, Rover, rovertrail_schema, rover_schema


def get_by_name(name):
    _rover = Rover.query.filter(Rover.name == name).one_or_none()
    if _rover is not None:
        return rover_schema.dump(_rover)
    else:
        return abort(404, "Rover not found.")


# def register(mac):
#     _rover_registered = Rover.query.filter(Rover.mac == mac).one_or_none()
#
#     if _rover_registered:
#         return "Rover registered", 200
#     else:
#         return abort(406, "New rover registration.")


# def update_gps(gps_data):
#     if gps_data:
#         return "Rover registered", 201
#     else:
#         return abort(406, "New rover registration.")


# def format_utc_time(time_str):
#     if not time_str:
#         return None
#     try:
#         # GPRMC time format is HHMMSS.sss
#         hour = time_str[0:2]
#         minute = time_str[2:4]
#         second = time_str[4:6]
#         return f"{hour}:{minute}:{second} UTC"
#     except Exception:
#         return time_str

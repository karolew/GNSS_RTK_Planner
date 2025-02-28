from flask import abort
from datetime import datetime


ROVERS = {
    "1": {
        "mac": "123",
        "name": "Rover1",
        "last_active": "2025-02-28 23:01:19.812781"
     }
}


def get_by_name(name):
    if name in ROVERS:
        return ROVERS.get(name), 200
    else:
        return abort(404, "Rover not found.")


def register(rover):
    rover_mac = rover.get("mac")

    if rover_mac in ROVERS:
        return "Rover registered", 201
    else:
        return abort(406, "New rover registration.")


def update_gps(gps_data):
    if gps_data:
        return "Rover registered", 201
    else:
        return abort(406, "New rover registration.")


def format_utc_time(time_str):
    if not time_str:
        return None
    try:
        # GPRMC time format is HHMMSS.sss
        hour = time_str[0:2]
        minute = time_str[2:4]
        second = time_str[4:6]
        return f"{hour}:{minute}:{second} UTC"
    except Exception:
        return time_str

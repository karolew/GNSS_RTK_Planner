from flask import abort, make_response, request, jsonify
from model import RoverTrail, Rover, rover_with_trails_schema, rovers_schema, trail_with_rovers_schema, rover_schema
from config import sqla
import json
from datetime import datetime

latest_gps_data = {
    "fix_status": "Unknown",
    "latitude": None,
    "longitude": None,
    "lat_raw": None,
    "lon_raw": None,
    "speed": None,
    "course": None,
    "time_utc": None,
    "last_update": None
}


def get_by_name(name):
    _rover = Rover.query.filter(Rover.name == name).one_or_none()
    if _rover is not None:
        return rover_schema.dump(_rover)
    else:
        return abort(404, "Rover not found.")


def get_all():
    _rovers = Rover.query.all()
    return rovers_schema.dump(_rovers)


def register(mac):
    mac_dict = json.loads(mac)
    _rover_registered = Rover.query.filter(Rover.mac == mac_dict.get("mac")).one_or_none()

    if _rover_registered:
        return "Rover registered", 200
    else:
        return abort(406, "Rover not registered.")


def update_gps(gnssdata):
    gnssdata_dict = json.loads(gnssdata)
    if gnssdata_dict:
        latest_gps_data.update(gnssdata_dict)
        latest_gps_data["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"""
        GPS Status Update:
        Fix Status: {gnssdata_dict["fix_status"]}
        Time (UTC): {format_utc_time(gnssdata_dict["time_utc"])}
        Raw Coordinates: {gnssdata_dict["lat_raw"]} / {gnssdata_dict["lon_raw"]}
        Decimal Coordinates: {gnssdata_dict["latitude"]}, {gnssdata_dict["longitude"]}
        Speed: {gnssdata_dict["speed"]} knots
        Course: {gnssdata_dict["course"]} degrees
        """)
        return "GPS Updated", 201
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
    except:
        return time_str
from flask import abort, make_response, request, jsonify
from model import RoverTrail, Rover, rover_with_trails_schema, rovers_schema, trail_with_rovers_schema, rover_schema, Trail
from config import sqla
import json
from datetime import datetime
from config import sqla

latest_gps_data = {
    "mac": None,
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


def get_coords():
    return jsonify(latest_gps_data)


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
        Rover MAC: {gnssdata_dict["mac"]}
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


def check_mac_exists(mac: str):
    exists = Rover.query.filter(Rover.mac == mac).first() is not None
    return {"exists": exists}


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


def create_rover():
    """Create a new rover with associated trails using SQLAlchemy"""
    data = request.get_json()

    # Check if MAC already exists using SQLAlchemy query
    if Rover.query.filter(Rover.mac == data['mac']).first() is not None:
        return {"error": "MAC address already exists"}, 400

    # Create new rover object
    new_rover = Rover(
        mac=data['mac'],
        name=data['name'],
        status='Idle',                  # Default status
        last_active=datetime.now(),     # TODO change to sth different
        trails = []
    )

    # Associate trails if provided
    if 'trail_ids' in data and data['trail_ids']:
        # Query all selected trails at once using SQLAlchemy
        trails = sqla.session.query(Trail).filter(Trail.id.in_(data['trail_ids'])).all()
        new_rover.trails = trails

    # Add to session and commit the transaction
    sqla.session.add(new_rover)
    sqla.session.commit()

    # Return the new rover
    return rover_schema.dump(new_rover)

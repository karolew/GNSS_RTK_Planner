from flask import Flask, render_template, request, jsonify
from datetime import datetime
import logging
import json
import config

app = Flask(__name__)
# app = config.connex_app
# app.add_api(config.basedir / "swagger.yaml")
logging.basicConfig(level=logging.INFO)


# Store the latest GPS data
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


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/update_gps", methods=["POST"])
def update_gps():
    data = request.json
    data = json.loads(data)
    latest_gps_data.update(data)
    latest_gps_data["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Log the GPS information
    app.logger.info(f"""
    GPS Status Update:
    Fix Status: {data["fix_status"]}
    Time (UTC): {format_utc_time(data["time_utc"])}
    Raw Coordinates: {data["lat_raw"]} / {data["lon_raw"]}
    Decimal Coordinates: {data["latitude"]}, {data["longitude"]}
    Speed: {data["speed"]} knots
    Course: {data["course"]} degrees
    """)

    return jsonify({"status": "success"})


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    data = json.loads(data)
    mac = data.get("mac")
    if mac == "a8032a56ae8c":                   # Hardcoded data
        print(f"Device registered: {mac}")
        return jsonify({"status": "success"}), 200
    else:
        print(f"Register the device first: {mac}")
        return jsonify({"status": "failure"}), 400

@app.route("/get_coords")
def get_coords():
    return jsonify(latest_gps_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
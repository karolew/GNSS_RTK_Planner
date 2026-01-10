import datetime
import json
import os
import queue
import sqlite3

from flask import Flask, Response, abort, g, jsonify, render_template, request

DATABASE = "rovers.db"
DATABASE_SCHEMA = "schema.sql"

# Queue to store data from connected rovers.
rover_data_queue = queue.Queue()

app = Flask(__name__)


# Database helper functions
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # DB cursor returns dict instead of tuple.
    return g.db


@app.teardown_appcontext
def close_connection(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource(DATABASE_SCHEMA, mode="r") as f:
            db.cursor().executescript(f.read())
        db.commit()


def query_db(query, args=(), one=False):
    cursor = get_db().execute(query, args)
    read_data = cursor.fetchall()
    cursor.close()
    return (read_data[0] if read_data else None) if one else read_data


def modify_db(query, args=()):
    conn = get_db()
    conn.execute(query, args)
    conn.commit()


# Routes
@app.route("/")
def index():
    return render_template("index.html")


# API routes
@app.route("/api/rovers", methods=["GET"])
def get_rovers():
    rovers = query_db("SELECT * FROM rover ORDER BY id DESC")
    return jsonify([dict(rover) for rover in rovers])


@app.route("/api/rovers", methods=["POST"])
def create_rover():
    data = request.json
    name = data.get("name")
    mac = data.get("mac")
    status = data.get("status", "inactive")
    last_active = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not name or not mac:
        return jsonify({"error": "Name and MAC address are required"}), 400

    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO rover (mac, name, status, last_active) VALUES (?, ?, ?, ?)",
            (mac, name, status, last_active)
        )
        rover_id = cursor.lastrowid
        conn.commit()

        # Get the newly created rover
        rover = query_db("SELECT * FROM rover WHERE id = ?", [rover_id], one=True)
        return jsonify(dict(rover))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/rovers/<int:rover_id>", methods=["GET"])
def get_rover(rover_id):
    rover = query_db("SELECT * FROM rover WHERE id = ?", [rover_id], one=True)
    if rover is None:
        return jsonify({"error": "Rover not found"}), 404
    return jsonify(dict(rover))


@app.route("/api/rovers/<int:rover_id>", methods=["PUT"])
def update_rover(rover_id):
    data = request.json
    name = data.get("name")
    mac = data.get("mac")

    if not name or not mac:
        return jsonify({"error": "Name and MAC address are required"}), 400

    try:
        modify_db(
            "UPDATE rover SET name = ?, mac = ? WHERE id = ?",
            (name, mac, rover_id)
        )

        # Get the updated rover
        rover = query_db("SELECT * FROM rover WHERE id = ?", [rover_id], one=True)
        if rover is None:
            return jsonify({"error": "Rover not found"}), 404
        return jsonify(dict(rover))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/rovers/<int:rover_id>", methods=["DELETE"])
def delete_rover(rover_id):
    try:
        # First delete associations
        modify_db("DELETE FROM rover_trail WHERE rover_id = ?", [rover_id])
        # Then delete the rover
        modify_db("DELETE FROM rover WHERE id = ?", [rover_id])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/trails", methods=["GET"])
def get_trails():
    trails = query_db("SELECT * FROM trail ORDER BY name")
    return jsonify([dict(trail) for trail in trails])


@app.route("/api/trails", methods=["POST"])
def create_trail():
    data = request.json
    name = data.get("name")
    trail_points = data.get("trail_points")

    if not name or not trail_points:
        return jsonify({"error": "Name and trail points are required"}), 400

    try:
        # Convert trail_points to proper JSON string
        trail_points_json = json.dumps(trail_points)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO trail (name, trail_points) VALUES (?, ?)",
            (name, trail_points_json)
        )
        trail_id = cursor.lastrowid
        conn.commit()

        # Get the newly created trail
        trail = query_db("SELECT * FROM trail WHERE id = ?", [trail_id], one=True)
        return jsonify(dict(trail))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/trails/<string:trail_name>", methods=["DELETE"])
def delete_trail(trail_name):
    try:
        trail_row = query_db("SELECT id FROM trail WHERE name = ?", [trail_name], one=True)
        trail_id = dict(trail_row).get("id")
        # First delete associations
        modify_db("DELETE FROM rover_trail WHERE trail_id = ?", [trail_id])
        # Then delete the trail
        modify_db("DELETE FROM trail WHERE name = ?", [trail_name])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/rovers/<int:rover_id>/trails", methods=["GET"])
def get_rover_trails(rover_id):
    trails = query_db("""
        SELECT t.* FROM trail t
        JOIN rover_trail rt ON t.id = rt.trail_id
        WHERE rt.rover_id = ?
        ORDER BY t.name
    """, [rover_id])
    return jsonify([dict(trail) for trail in trails])


@app.route("/api/rovers/<int:rover_id>/trails", methods=["POST"])
def add_trail_to_rover(rover_id):
    data = request.json
    trail_id = data.get("trail_id")

    if not trail_id:
        return jsonify({"error": "Trail ID is required"}), 400

    # Check if the association already exists
    existing = query_db(
        "SELECT 1 FROM rover_trail WHERE rover_id = ? AND trail_id = ?",
        [rover_id, trail_id],
        one=True
    )

    if existing:
        return jsonify({"error": "Trail is already associated with this rover"}), 400

    try:
        modify_db(
            "INSERT INTO rover_trail (rover_id, trail_id) VALUES (?, ?)",
            (rover_id, trail_id)
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/rovers/<int:rover_id>/trails/<int:trail_id>", methods=["DELETE"])
def remove_trail_from_rover(rover_id, trail_id):
    try:
        modify_db(
            "DELETE FROM rover_trail WHERE rover_id = ? AND trail_id = ?",
            (rover_id, trail_id)
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    "last_update": None,
    "sv": None,
    "su": None
}


@app.route("/rover/get_coords", methods=["GET"])
def get_coords():
    def event_stream():
        while True:
            # Get data from the queue and send
            data = rover_data_queue.get()
            yield f"data: {json.dumps(data)}\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


@app.route("/rover/update_gps", methods=["POST"])
def update_gps():
    data = request.json
    gnssdata_dict = json.loads(data)
    if gnssdata_dict:
        latest_gps_data.update(gnssdata_dict)
        latest_gps_data["last_update"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Rover MAC: {gnssdata_dict['mac']}, "
              f"{gnssdata_dict['fix_status']}, "
              f"({gnssdata_dict['latitude']}, "
              f"{gnssdata_dict['longitude']})\n"
              f"Sat in Use: {gnssdata_dict['su']}\n",
              f"Sat in View: {gnssdata_dict['sv']}")

        rover_data_queue.put(latest_gps_data)
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


@app.route("/rover/register", methods=["POST"])
def register():
    data = request.json
    mac_dict = json.loads(data)
    mac = mac_dict.get("mac")
    print(f"Rover trying to connect, MAC: {mac}")
    rovers = query_db("SELECT * FROM rover ORDER BY id DESC")
    rovers_list = [dict(rover) for rover in rovers]
    _rover_registered = any([rover.get("mac") == mac for rover in rovers_list])
    if _rover_registered:
        return "Rover registered", 200
    else:
        return abort(406, "Rover not registered.")


#  HTTP polling to update rover with trails.
#  Simplest approach for demo purpose. Consider sockets or mqtt.
#
#  get_data = the Rover is pulling data every few seconds. trails are stored in trail_points_for_rover.
#  upload_trail_to_rover - prepare get trails from database and put into trail_points_for_rover.
#  stop_rover - send empty trails to the Rover.
trail_points_for_rover = {"mac": "", "trail_points": ""}


@app.route("/trail/upload/<int:rover_id>/<int:trail_id>/<int:precision>", methods=["POST"])
def upload_trail_to_rover(rover_id, trail_id, precision):
    global trail_points_for_rover
    rover_mac = query_db("SELECT mac FROM rover WHERE id = ?", [rover_id], one=True)
    trail_points = query_db("SELECT trail_points FROM trail WHERE id = ?", [trail_id], one=True)
    trail_points_dict = dict(trail_points)
    trail_points_for_rover = dict(rover_mac)
    trail_points_for_rover.update({"precision" : precision})
    trail_points_for_rover.update(trail_points_dict)
    if trail_points_for_rover["mac"] and trail_points_dict["trail_points"]:
        return trail_points_for_rover, 200
    else:
        return abort(400, "No trails to send.")


@app.route("/trail/stop/<int:rover_id>", methods=["POST"])
def stop_rover(rover_id):
    global trail_points_for_rover
    rover_mac = query_db("SELECT mac FROM rover WHERE id = ?", [rover_id], one=True)
    trail_points_for_rover = dict(rover_mac)
    trail_points_for_rover.update({"trail_points": "[]"})
    if rover_mac:
        return trail_points_for_rover, 200
    else:
        return abort(400, f"Rover does not exist {rover_id} {rover_mac}.")


@app.route("/trail/upload", methods=["GET"])
def get_data():
    global trail_points_for_rover
    tmp = trail_points_for_rover
    trail_points_for_rover = {"mac": "", "trail_points": ""}
    return jsonify(tmp)


if __name__ == "__main__":
    # Create schema.sql file.
    if not os.path.exists(DATABASE_SCHEMA):
        with open(DATABASE_SCHEMA, "w") as f:
            f.write("""
    -- Schema for Rover Management Database

    -- Rover table
    CREATE TABLE IF NOT EXISTS rover (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mac TEXT NOT NULL,
        name TEXT NOT NULL,
        status TEXT DEFAULT "inactive",
        last_active TEXT
    );

    -- Trail table
    CREATE TABLE IF NOT EXISTS trail (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        trail_points TEXT
    );

    -- Rover-Trail association table
    CREATE TABLE IF NOT EXISTS rover_trail (
        rover_id INTEGER,
        trail_id INTEGER,
        PRIMARY KEY (rover_id, trail_id),
        FOREIGN KEY (rover_id) REFERENCES rover(id) ON DELETE CASCADE,
        FOREIGN KEY (trail_id) REFERENCES trail(id) ON DELETE CASCADE
    );

    -- Insert some sample
    INSERT OR IGNORE INTO rover (id, name, mac, status, last_active) VALUES
        (1, "Rover1", "a8032a56ae8c", "Inactive", "2025-01-01 22:22:22.22");
    INSERT OR IGNORE INTO trail (id, name, trail_points) VALUES
        (1, "Example Trail", "[[45.123, -122.456], [45.124, -122.457]]");
    """)
    if not os.path.exists(DATABASE):
        init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)

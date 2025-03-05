from flask import render_template, request, jsonify
import config
import json
import rover
import datetime

app = config.connex_app
app.add_api(config.basedir / "swagger.yaml")


@app.route("/")
def home():
    all_rovers = rover.get_all()
    return render_template("index.html", rovers=all_rovers)


@app.route("/get_coords")
def get_coords():
    return jsonify(rover.latest_gps_data)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

from flask import render_template
import config
from model import Rover

app = config.connex_app
app.add_api(config.basedir / "swagger.yaml")


@app.route("/")
def home():
    rovers = Rover.query.all()
    return render_template("index.html", rovers=rovers)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

import pathlib
import connexion
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy


basedir = pathlib.Path(__file__).parent.resolve()
connex_app = connexion.App(__name__, specification_dir="/")


app = connex_app.app

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{basedir / 'rover.db'}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

sqla = SQLAlchemy(app)
mars = Marshmallow(app)

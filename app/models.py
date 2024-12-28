from os import getenv

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(engine_options={"url": getenv("SQLALCHEMY_DATABASE_URI")})


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    hashed_password = db.Column(db.String(128), nullable=False)
    balance = db.Column(db.Float, default=0.0)

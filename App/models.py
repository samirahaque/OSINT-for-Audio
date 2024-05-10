from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Agent(db.Model):
    __tablename__ = 'agents'
    id = db.Column(db.Integer, primary_key=True)
    key_no = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)

class WazuhCredentials(db.Model):
    __bind_key__ = 'wazuhdb'
    __tablename__ = 'wazuh_credentials'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)

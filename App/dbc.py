from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__, instance_relative_config=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'agents.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Agent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key_no = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)

os.makedirs(app.instance_path, exist_ok=True)

def add_agent(key_no, name):
    # Check if an agent with the given key_no already exists
    existing_agent = Agent.query.filter_by(key_no=key_no).first()
    if not existing_agent:
        new_agent = Agent(key_no=key_no, name=name)
        db.session.add(new_agent)
        db.session.commit()
        print(f"Added new agent: {name} with key_no: {key_no}")
    else:
        print(f"Agent with key_no: {key_no} already exists.")

with app.app_context():
    db.create_all()
    # Example: Add an agent with key_no "156" and name "Muhammad Ayub"
    add_agent("156", "Muhammad Ayub")
    print("Database and tables created in the instance directory.")

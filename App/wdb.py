from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Setup Flask application and SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.getcwd(), 'wdb.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define the WazuhCredentials model
class WazuhCredentials(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)
    url = db.Column(db.String(255), nullable=False)

# Function to add or update Wazuh credentials
def add_or_update_credentials(username, password, url):
    with app.app_context():
        # Check if any credentials exist
        credential = WazuhCredentials.query.first()
        if credential:
            # Update existing credentials
            credential.username = username
            credential.password = password
            credential.url = url
            print("Updated existing Wazuh credentials.")
        else:
            # Insert new credentials
            new_credential = WazuhCredentials(username=username, password=password, url=url)
            db.session.add(new_credential)
            print("Added new Wazuh credentials.")
        db.session.commit()

# Initialize the database and add/update credentials
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Creates tables

    # Add or update Wazuh credentials
    # Replace the values with your actual Wazuh credentials and URL
    add_or_update_credentials('admin', '9VDeqBcu76Eby?7rEJ2Aw6U3d*mbStKl', 'https://199.200.240.249')
    print("Database setup complete.")

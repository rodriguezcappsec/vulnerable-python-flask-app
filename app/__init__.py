from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import timedelta

app = Flask(__name__)
app.config["SECRET_KEY"] = "your-secret-key"

# Set session lifetime to 30 minutes (for demonstration purposes)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

# Other settings...
app.config["SESSION_COOKIE_SECURE"] = False  # Insecure: Not HTTPS-only
app.config["SESSION_COOKIE_HTTPONLY"] = False  # Insecure: Accessible via JavaScript
app.config["SESSION_COOKIE_SAMESITE"] = None  # Insecure: No cross-site restriction

# SQLite database setup: store the database file in the project directory
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"sqlite:///{os.path.join(base_dir, 'vulnerable_app.db')}"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

from app import routes  # Ensure this imports your routes

from flask import Flask

# Create the Flask application
app = Flask(__name__)

# Import routes (this ensures routes are registered with the app)
from app import main
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

from flask_app import routes, models

"""
Flask shell commands:
flask db init (initialize database)
flask db migrate (create migration script after modifying db)
flask db upgrade (execute migration script)
flask db downgrade (undo last migration)
"""
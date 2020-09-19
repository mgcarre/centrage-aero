"""Package initialization
"""

import os

from flask import Flask
from flask_session import Session


def create_app():
    """Flask app"""
    app = Flask(__name__)
    if os.environ["FLASK_ENV"].lower() in ["dev", "development"]:
        app.config.from_object("prepavol.config.DevelopmentConfig")
    elif os.environ["FLASK_ENV"].lower() in ["test", "testing"]:
        app.config.from_object("prepavol.config.TestingConfig")
    elif os.environ["FLASK_ENV"].lower() in ["prod", "production"]:
        app.config.from_object("prepavol.config.ProductionConfig")
    else:
        app.config.from_object("prepavol.config.Config")

    Session(app)

    # Registrations
    # blueprint for non-auth parts of app
    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    return app

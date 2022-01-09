"""Package initialization."""

__author__ = "Yannick Teresiak"
__copyright__ = "Copyright 2020, Prepavol"
__credits__ = ["Yannick Teresiak"]
__license__ = None
__version__ = "2.4"
__maintainer__ = "Yannick Teresiak"
__email__ = "yannick.teresiak@gmail.com"
__status__ = "Production"

import os

from flask import Flask
from flask_session import Session
import prepavol.logbook
import prepavol.planes
from .main import main as main_blueprint
from flask_wtf.csrf import CSRFProtect

__all__ = ["logbook", "planes"]
csrf = CSRFProtect()

def create_app():
    """Flask app."""
    app = Flask(__name__)
    csrf.init_app(app)
    if os.environ["FLASK_ENV"].lower() in ["dev", "development"]:
        app.config.from_object("prepavol.config.DevelopmentConfig")
    elif os.environ["FLASK_ENV"].lower() in ["test", "testing"]:
        app.config.from_object("prepavol.config.TestingConfig")
    elif os.environ["FLASK_ENV"].lower() in ["prod", "production"]:
        app.config.from_object("prepavol.config.ProductionConfig")
    else:
        app.config.from_object("prepavol.config.Config")

    sess = Session()
    sess.init_app(app)
    
    # Registrations
    # blueprint for non-auth parts of app
    app.register_blueprint(main_blueprint)

    return app

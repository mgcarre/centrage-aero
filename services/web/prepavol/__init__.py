"""Package initialization
"""

from flask import Flask


def create_app():
    """Flask app"""
    app = Flask(__name__)
    app.config.from_object("prepavol.config.Config")

    # Registrations
    # blueprint for non-auth parts of app
    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    return app

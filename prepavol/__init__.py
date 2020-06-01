from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "nosecret"
    # app.config['EXPLAIN_TEMPLATE_LOADING'] = True

    # Registrations
    # blueprint for non-auth parts of app
    from .main import main as main_blueprint

    app.register_blueprint(main_blueprint)

    return app

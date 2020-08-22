from flask import Flask

from gm.main.config import app_config


def create_app():
    """
    This function builds the Flask API and initializes the API with the database
    configurations (in the config.py), the API blueprints (where we define the API
    endpoints and map the code for each endpoint) and finally we try to initiate the
    app with the Database Model (our database model defined in code using SQLAlchemy).

    :return: the initialized app
    """
    app = Flask(__name__)
    app.config.from_object(app_config['development'])

    from gm.main.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/v1/monitoring')

    from gm.main.models.model import db
    app.app_context().push()
    db.init_app(app)
    db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.app_context().push()
    app.run(debug=True, host='0.0.0.0', port='5000', threaded=True)

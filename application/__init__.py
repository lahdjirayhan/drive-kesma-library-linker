# pylint: disable=wrong-import-position, import-outside-toplevel

import logging
logging.basicConfig(level=logging.WARNING)

from decouple import config

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_talisman import Talisman
from application.configuration import Configuration
from application.drive_linker import drive

db = SQLAlchemy()
migrate = Migrate()
talisman = Talisman()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Configuration)

    # Imported to make sure flask-migrate recognizes the models
    # pylint: disable=unused-import
    from application import models

    # Initialize flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    talisman.init_app(app)

    # Add mastermind
    from application.master import Mastermind
    app.config['mastermind'] = Mastermind(drive, db)

    # Register blueprints
    from application.auth.routes import auth
    from application.linebot.routes import line_callback

    app.register_blueprint(auth)
    app.register_blueprint(line_callback)

    return app

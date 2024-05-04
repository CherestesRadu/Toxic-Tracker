import os
from flask import Flask
from .riot import RiotApi
from .config import (RIOT_API_KEY, DB_KEY)
from .db import *
import sqlite3

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY= DB_KEY,
        DATABASE=os.path.join(app.instance_path, 'backend.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    riot_api = RiotApi(RIOT_API_KEY, 'europe')

    from . import db
    db.init_app(app)

    from . import player
    app.register_blueprint(player.blueprint)

    return app
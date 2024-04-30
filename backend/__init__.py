import os
from flask import Flask
from .riot import RiotApi
from config import RIOT_API_KEY


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
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

    @app.route('/')
    def testing():
        matches = riot_api.get_matches_from_puuid('ubD8VSQx-85GcWmO8UbSqz2kaex8zw2FSaSaOGRgQ_FJ_YdGqlZohc7bLGbUKGMJlDSAFPNBFu-PWQ')
        match_stats = []
        for match in matches:
            match_stats.append(riot_api.get_match_stats(match))
            
        return match_stats
    return app
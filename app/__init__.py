import os
from flask import Flask
from config import config_by_name
from .extensions import db, migrate, jwt, cors
from flasgger import Swagger
from .routes import register_routes

def create_app():
    app = Flask(__name__)

    # Charger la configuration en fonction de l'environnement
    env = os.getenv("FLASK_ENV", "development")  # Par défaut : développement
    app.config.from_object(config_by_name[env])

    app.config['SWAGGER'] = {
        'title': 'API Documentation',
        'uiversion': 3,
        'specs_route': '/docs/'  # URL pour accéder à la documentation
    }
    swagger = Swagger(app)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)

    register_routes(app)

    return app

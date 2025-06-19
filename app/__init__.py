import os
from flask import Flask
from config import config_by_name
from .extensions import db, migrate, jwt, cors
from .routes import register_routes

def create_app():
    app = Flask(__name__)

    # Charger la configuration en fonction de l'environnement
    env = os.getenv("FLASK_ENV", "development")  # Par défaut : développement
    app.config.from_object(config_by_name[env])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)

    register_routes(app)

    return app

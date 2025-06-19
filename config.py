from datetime import timedelta
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Config:
    """Configuration de base."""
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default_jwt_secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7) 

    # Chargement de l'URL de la base de données depuis les variables d'environnement
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

class DevelopmentConfig(Config):
    """Configuration pour le développement."""
    DEBUG = True

class ProductionConfig(Config):
    """Configuration pour la production."""
    DEBUG = False

# Dictionnaire de mapping des configurations
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig
}

from flask import Blueprint

# Importation des blueprints
from .auth import auth_bp
from .user import user_bp
from .movie import movie_bp
from .rating import rating_bp
from .recommendation import recommendation_bp
from .watchlist import watchlist_bp
from .favorite import favorite_bp
from .role import role_bp
from .accesstatic import access_bp
from .like import like_bp
from .review import review_bp
# Création d'un blueprint principal
main_bp = Blueprint('main', __name__)

# Enregistrement des blueprints dans une liste
def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(movie_bp)
    app.register_blueprint(rating_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(watchlist_bp)
    app.register_blueprint(favorite_bp)
    app.register_blueprint(role_bp)
    app.register_blueprint(access_bp)
    app.register_blueprint(like_bp)
    app.register_blueprint(review_bp)

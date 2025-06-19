from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.favorite import Favorite
from app.models.user import User
from app.models.movie import Movie

favorite_bp = Blueprint('favorite', __name__, url_prefix='/favorites')

@favorite_bp.route('/', methods=['GET'])
def get_all_favorites():
    """Récupérer tous les favoris"""
    favorites = Favorite.query.all()
    return jsonify([{"id": f.id, "user_id": f.user_id, "movie_id": f.movie_id} for f in favorites])

@favorite_bp.route('/<int:user_id>', methods=['GET'])
def get_user_favorites(user_id):
    """Récupérer les favoris d’un utilisateur spécifique"""
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    return jsonify([{"id": f.id, "movie_id": f.movie_id} for f in favorites])

@favorite_bp.route('/', methods=['POST'])
def add_favorite():
    """Ajouter un film aux favoris"""
    data = request.get_json()
    user_id = data.get('user_id')
    movie_id = data.get('movie_id')

    if not user_id or not movie_id:
        return jsonify({"error": "user_id et movie_id sont requis"}), 400

    favorite = Favorite(user_id=user_id, movie_id=movie_id)
    db.session.add(favorite)
    db.session.commit()
    
    return jsonify({"message": "Favori ajouté avec succès"}), 201

@favorite_bp.route('/<int:id>', methods=['DELETE'])
def delete_favorite(id):
    """Supprimer un favori"""
    favorite = Favorite.query.get(id)
    if not favorite:
        return jsonify({"error": "Favori non trouvé"}), 404

    db.session.delete(favorite)
    db.session.commit()
    
    return jsonify({"message": "Favori supprimé"}), 200

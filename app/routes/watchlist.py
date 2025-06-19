from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.watchlist import Watchlist

watchlist_bp = Blueprint('watchlist', __name__, url_prefix='/watchlist')

@watchlist_bp.route('/', methods=['POST'])
@jwt_required()
def add_to_watchlist():
    """Ajouter un film à sa watchlist"""
    user_id = get_jwt_identity()
    data = request.get_json()
    movie_id = data.get('movie_id')

    if not movie_id:
        return jsonify({"error": "ID du film requis"}), 400

    existing_entry = Watchlist.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if existing_entry:
        return jsonify({"error": "Film déjà dans la watchlist"}), 400

    entry = Watchlist(user_id=user_id, movie_id=movie_id)
    db.session.add(entry)
    db.session.commit()

    return jsonify({"message": "Film ajouté à la watchlist"}), 201

@watchlist_bp.route('/', methods=['GET'])
@jwt_required()
def get_watchlist():
    """Voir sa watchlist"""
    user_id = get_jwt_identity()
    watchlist = Watchlist.query.filter_by(user_id=user_id).all()

    if not watchlist:
        return jsonify({"message": "Votre watchlist est vide"}), 404

    return jsonify([{"movie_id": w.movie_id} for w in watchlist])

@watchlist_bp.route('/<int:movie_id>', methods=['DELETE'])
@jwt_required()
def remove_from_watchlist(movie_id):
    """Supprimer un film de sa watchlist"""
    user_id = get_jwt_identity()

    entry = Watchlist.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if not entry:
        return jsonify({"error": "Ce film n'est pas dans votre watchlist"}), 404

    db.session.delete(entry)
    db.session.commit()

    return jsonify({"message": "Film retiré de la watchlist"})

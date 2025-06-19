# app/routes/like.py

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.like import Like

like_bp = Blueprint('like', __name__, url_prefix='/likes')

@like_bp.route('/<int:movie_id>', methods=['POST'])
@jwt_required()
def like_movie(movie_id):
    user_id = get_jwt_identity()
    existing = Like.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if existing:
        return jsonify({"message": "Déjà liké"}), 400

    new_like = Like(user_id=user_id, movie_id=movie_id)
    db.session.add(new_like)
    db.session.commit()
    return jsonify({"message": "Film liké"}), 201

@like_bp.route('/<int:movie_id>', methods=['DELETE'])
@jwt_required()
def unlike_movie(movie_id):
    user_id = get_jwt_identity()
    like = Like.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if not like:
        return jsonify({"message": "Pas encore liké"}), 404

    db.session.delete(like)
    db.session.commit()
    return jsonify({"message": "Like supprimé"})

@like_bp.route('/<int:movie_id>/status', methods=['GET'])
@jwt_required()
def check_like(movie_id):
    user_id = get_jwt_identity()
    liked = Like.query.filter_by(user_id=user_id, movie_id=movie_id).first() is not None
    return jsonify({"liked": liked})

@like_bp.route('/<int:movie_id>/count', methods=['GET'])
@jwt_required()
def like_count(movie_id):
    count = Like.query.filter_by(movie_id=movie_id).count()
    return jsonify({"like_count": count})
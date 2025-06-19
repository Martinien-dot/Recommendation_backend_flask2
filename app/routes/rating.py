from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.rating import Rating

rating_bp = Blueprint('rating', __name__, url_prefix='/ratings')

@rating_bp.route('/', methods=['POST'])
@jwt_required()
def add_rating():
    user_id = get_jwt_identity()
    data = request.get_json()
    movie_id = data.get('movie_id')
    rating = data.get('rating')

    if not movie_id or rating is None:
        return jsonify({"error": "ID du film et note requis"}), 400

    existing = Rating.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if existing:
        existing.rating = rating
    else:
        new_rating = Rating(user_id=user_id, movie_id=movie_id, rating=rating)
        db.session.add(new_rating)

    db.session.commit()
    return jsonify({"message": "Note enregistrée"}), 200

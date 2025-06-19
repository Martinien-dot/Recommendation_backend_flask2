from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.review import Review
from app.models.movie import Movie

review_bp = Blueprint('review', __name__, url_prefix='/reviews')

# 🔁 Fonction pour recalculer la note moyenne d’un film
def update_movie_rating(movie_id):
    reviews = Review.query.filter_by(movie_id=movie_id).all()
    movie = Movie.query.get(movie_id)

    if not movie:
        return

    if reviews:
        average_rating = sum([r.rating for r in reviews if r.rating is not None]) / len(reviews)
        movie.rating = round(average_rating, 2)
    else:
        movie.rating = None  # Aucun avis => pas de note

    db.session.commit()

@review_bp.route('/', methods=['POST'])
@jwt_required()
def add_review():
    """Ajouter un avis à un film"""
    user_id = get_jwt_identity()
    data = request.get_json()

    movie_id = data.get('movie_id')
    review_text = data.get('review_text')
    rating = data.get('rating')

    if not movie_id or not review_text or rating is None:
        return jsonify({"error": "ID du film, avis et note requis"}), 400

    try:
        rating = float(rating)
        if not (0 <= rating <= 5):
            raise ValueError()
    except:
        return jsonify({"error": "La note doit être un nombre entre 0 et 5"}), 400

    existing_review = Review.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if existing_review:
        return jsonify({"error": "Vous avez déjà laissé un avis sur ce film"}), 400

    review = Review(user_id=user_id, movie_id=movie_id, review_text=review_text, rating=rating)
    db.session.add(review)
    db.session.commit()

    update_movie_rating(movie_id)

    return jsonify({
        "message": "Avis ajouté",
        "review": {
            "user_id": review.user_id,
            "movie_id": review.movie_id,
            "review_text": review.review_text,
            "rating": review.rating,
            "timestamp": review.timestamp.isoformat()
        }
    }), 201

@review_bp.route('/<int:movie_id>', methods=['GET'])
def get_movie_reviews(movie_id):
    """Obtenir tous les avis pour un film"""
    reviews = Review.query.filter_by(movie_id=movie_id).all()
    if not reviews:
        return jsonify({"message": "Aucun avis trouvé pour ce film"}), 404

    return jsonify({
        "movie_id": movie_id,
        "reviews": [
            {
                "user_id": r.user_id,
                "review_text": r.review_text,
                "rating": r.rating,
                "timestamp": r.timestamp.isoformat()
            } for r in reviews
        ]
    })

@review_bp.route('/<int:movie_id>', methods=['PUT'])
@jwt_required()
def update_review(movie_id):
    """Modifier son avis sur un film"""
    user_id = get_jwt_identity()
    data = request.get_json()
    review_text = data.get('review_text')
    rating = data.get('rating')

    if not review_text or rating is None:
        return jsonify({"error": "Texte et note requis"}), 400

    try:
        rating = float(rating)
        if not (0 <= rating <= 5):
            raise ValueError()
    except:
        return jsonify({"error": "La note doit être un nombre entre 0 et 5"}), 400

    review = Review.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if not review:
        return jsonify({"error": "Vous n'avez pas encore laissé d'avis pour ce film"}), 404

    review.review_text = review_text
    review.rating = rating
    db.session.commit()

    update_movie_rating(movie_id)

    return jsonify({"message": "Avis mis à jour", "new_review": review.review_text, "new_rating": review.rating})

@review_bp.route('/<int:movie_id>', methods=['DELETE'])
@jwt_required()
def delete_review(movie_id):
    """Supprimer son avis sur un film"""
    user_id = get_jwt_identity()

    review = Review.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if not review:
        return jsonify({"error": "Vous n'avez pas encore laissé d'avis pour ce film"}), 404

    db.session.delete(review)
    db.session.commit()

    update_movie_rating(movie_id)

    return jsonify({"message": "Avis supprimé"})


@review_bp.route('/<int:movie_id>/me', methods=['GET'])
@jwt_required()
def get_user_review(movie_id):
    """Obtenir l'avis de l'utilisateur connecté pour un film"""
    user_id = get_jwt_identity()
    review = Review.query.filter_by(user_id=user_id, movie_id=movie_id).first()
    if not review:
        return jsonify({"message": "Aucun avis trouvé"}), 404

    return jsonify({
        "user_id": review.user_id,
        "movie_id": review.movie_id,
        "review_text": review.review_text,
        "rating": review.rating,
        "timestamp": review.timestamp.isoformat()
    })
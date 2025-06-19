from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.review import Review
from app.models.movie import Movie
from typing import Any, Dict, List, Tuple, Union, Optional

review_bp = Blueprint('review', __name__, url_prefix='/reviews')

def update_movie_rating(movie_id: int) -> None:
    """
    Met à jour la note moyenne d'un film
    Args:
        movie_id: ID du film à mettre à jour
    """
    reviews = Review.query.filter_by(movie_id=movie_id).all()
    movie = Movie.query.get(movie_id)

    if not movie:
        return

    if reviews:
        average_rating = sum([r.rating for r in reviews if r.rating is not None]) / len(reviews)
        movie.rating = round(average_rating, 2)
    else:
        movie.rating = None

    db.session.commit()

@review_bp.route('/', methods=['POST'])
@jwt_required()
def add_review() -> Union[Dict[str, Any], Tuple[Dict[str, str], int]]:
    """
    Ajoute un nouvel avis à un film
    ---
    tags:
      - Avis
    security:
      - JWT: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - movie_id
            - review_text
            - rating
          properties:
            movie_id:
              type: integer
              description: ID du film
            review_text:
              type: string
              description: Contenu de l'avis
            rating:
              type: number
              description: Note entre 0 et 5
    responses:
      201:
        description: Avis créé avec succès
        schema:
          type: object
          properties:
            message:
              type: string
            review:
              type: object
              properties:
                user_id:
                  type: integer
                movie_id:
                  type: integer
                review_text:
                  type: string
                rating:
                  type: number
                timestamp:
                  type: string
                  format: date-time
      400:
        description: Données invalides ou avis déjà existant
    """
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
def get_movie_reviews(movie_id: int) -> Union[Dict[str, Any], Tuple[Dict[str, str], int]]:
    """
    Récupère tous les avis pour un film spécifique
    ---
    tags:
      - Avis
    parameters:
      - name: movie_id
        in: path
        type: integer
        required: true
        description: ID du film
    responses:
      200:
        description: Liste des avis pour le film
        schema:
          type: object
          properties:
            movie_id:
              type: integer
            reviews:
              type: array
              items:
                type: object
                properties:
                  user_id:
                    type: integer
                  review_text:
                    type: string
                  rating:
                    type: number
                  timestamp:
                    type: string
                    format: date-time
      404:
        description: Aucun avis trouvé pour ce film
    """
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
def update_review(movie_id: int) -> Union[Dict[str, Any], Tuple[Dict[str, str], int]]:
    """
    Met à jour l'avis d'un utilisateur sur un film
    ---
    tags:
      - Avis
    security:
      - JWT: []
    parameters:
      - name: movie_id
        in: path
        type: integer
        required: true
        description: ID du film
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - review_text
            - rating
          properties:
            review_text:
              type: string
              description: Nouveau contenu de l'avis
            rating:
              type: number
              description: Nouvelle note entre 0 et 5
    responses:
      200:
        description: Avis mis à jour avec succès
        schema:
          type: object
          properties:
            message:
              type: string
            new_review:
              type: string
            new_rating:
              type: number
      400:
        description: Données invalides
      404:
        description: Avis non trouvé
    """
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

    return jsonify({
        "message": "Avis mis à jour", 
        "new_review": review.review_text, 
        "new_rating": review.rating
    })

@review_bp.route('/<int:movie_id>', methods=['DELETE'])
@jwt_required()
def delete_review(movie_id: int) -> Union[Dict[str, str], Tuple[Dict[str, str], int]]:
    """
    Supprime l'avis d'un utilisateur sur un film
    ---
    tags:
      - Avis
    security:
      - JWT: []
    parameters:
      - name: movie_id
        in: path
        type: integer
        required: true
        description: ID du film
    responses:
      200:
        description: Avis supprimé avec succès
      404:
        description: Avis non trouvé
    """
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
def get_user_review(movie_id: int) -> Union[Dict[str, Any], Tuple[Dict[str, str], int]]:
    """
    Récupère l'avis d'un utilisateur spécifique pour un film
    ---
    tags:
      - Avis
    security:
      - JWT: []
    parameters:
      - name: movie_id
        in: path
        type: integer
        required: true
        description: ID du film
    responses:
      200:
        description: Avis de l'utilisateur
        schema:
          type: object
          properties:
            user_id:
              type: integer
            movie_id:
              type: integer
            review_text:
              type: string
            rating:
              type: number
            timestamp:
              type: string
              format: date-time
      404:
        description: Avis non trouvé
    """
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


@review_bp.route('/all', methods=['GET'])
def get_all_reviews() -> Union[Dict[str, Any], Tuple[Dict[str, str], int]]:
    """
    Récupère tous les avis avec pagination
    ---
    tags:
      - Avis
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: Numéro de page
      - name: per_page
        in: query
        type: integer
        required: false
        default: 10
        description: Nombre d'avis par page
      - name: sort
        in: query
        type: string
        required: false
        enum: [newest, oldest, highest, lowest]
        default: newest
        description: Ordre de tri
    responses:
      200:
        description: Liste paginée de tous les avis
        schema:
          type: object
          properties:
            reviews:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  user_id:
                    type: integer
                  movie_id:
                    type: integer
                  movie_title:
                    type: string
                  review_text:
                    type: string
                  rating:
                    type: number
                  timestamp:
                    type: string
                    format: date-time
            pagination:
              type: object
              properties:
                total:
                  type: integer
                pages:
                  type: integer
                current_page:
                  type: integer
                per_page:
                  type: integer
      500:
        description: Erreur serveur
    """
    try:
        # Récupération des paramètres de pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Récupération du paramètre de tri
        sort = request.args.get('sort', 'newest')
        
        # Construction de la requête de base
        query = Review.query.join(Movie, Review.movie_id == Movie.id)
        
        # Application du tri
        if sort == 'newest':
            query = query.order_by(Review.timestamp.desc())
        elif sort == 'oldest':
            query = query.order_by(Review.timestamp.asc())
        elif sort == 'highest':
            query = query.order_by(Review.rating.desc())
        elif sort == 'lowest':
            query = query.order_by(Review.rating.asc())
        
        # Exécution de la requête paginée
        paginated_reviews = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Formatage des résultats
        reviews_data = []
        for review in paginated_reviews.items:
            reviews_data.append({
                'id': review.id,
                'user_id': review.user_id,
                'movie_id': review.movie_id,
                'movie_title': review.movie.title if review.movie else 'Film inconnu',
                'review_text': review.review_text,
                'rating': review.rating,
                'timestamp': review.timestamp.isoformat()
            })
        
        return jsonify({
            'reviews': reviews_data,
            'pagination': {
                'total': paginated_reviews.total,
                'pages': paginated_reviews.pages,
                'current_page': paginated_reviews.page,
                'per_page': paginated_reviews.per_page
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
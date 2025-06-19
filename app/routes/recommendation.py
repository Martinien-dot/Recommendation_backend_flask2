# routes/recommendation_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.like import Like
from app.models.rating import Rating
from app.models.review import Review
from app.services.recommendation_service import RecommendationService
from app.models import Movie, User
from app.extensions import db

recommendation_bp = Blueprint('recommendations', __name__, url_prefix='/recommendations')
recommendation_service = RecommendationService()


@recommendation_bp.route('/', methods=['GET'])
@jwt_required()
def get_recommendations():
    """
    Récupère les recommandations pour l'utilisateur connecté
    """
    user_id = get_jwt_identity()
    method = request.args.get('method', 'hybrid')  # hybrid, collaborative, content
    limit = int(request.args.get('limit', 10))
    
    try:
        # Générer de nouvelles recommandations si demandé
        if request.args.get('refresh', 'false').lower() == 'true':
            recommendations = recommendation_service.generate_recommendations_for_user(
                user_id, method, limit
            )
        else:
            # Récupérer les recommandations existantes
            recommendations = recommendation_service.get_user_recommendations(user_id, limit)
            
            # Si aucune recommandation n'existe, en générer
            if not recommendations:
                recommendations = recommendation_service.generate_recommendations_for_user(
                    user_id, method, limit
                )
        
        # Enrichir avec les détails des films
        recommended_movies = []
        for movie_id, score in recommendations:
            movie = Movie.query.get(movie_id)
            if movie:
                recommended_movies.append({
                    'id': movie.id,
                    'title': movie.title,
                    'release_year': movie.release_year,
                    'rating': movie.rating,
                    'description': movie.description,
                    'poster_url': movie.poster_url,
                    'recommendation_score': round(score, 3),
                    'director': movie.director.name if movie.director else None,
                    'genres': [genre.name for genre in movie.genres]
                })
        
        return jsonify({
            'recommendations': recommended_movies,
            'method': method,
            'total': len(recommended_movies)
        })
        
    except Exception as e:
        return jsonify({'error': f'Erreur lors de la génération des recommandations: {str(e)}'}), 500


@recommendation_bp.route('/similar-users', methods=['GET'])
@jwt_required()
def get_similar_users():
    """
    Trouve les utilisateurs similaires à l'utilisateur connecté
    """
    user_id = get_jwt_identity()
    limit = int(request.args.get('limit', 5))
    
    try:
        user_movie_scores = recommendation_service.build_user_movie_matrix()
        
        if user_id not in user_movie_scores:
            return jsonify({'similar_users': [], 'message': 'Pas assez de données'})
        
        target_user_scores = user_movie_scores[user_id]
        similarities = {}
        
        for other_user_id, scores in user_movie_scores.items():
            if other_user_id != user_id:
                similarity = recommendation_service.calculate_user_similarity(
                    target_user_scores, scores
                )
                if similarity > 0:
                    similarities[other_user_id] = similarity
        
        # Trier par similarité décroissante
        similar_users = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        # Enrichir avec les détails des utilisateurs
        result = []
        for other_user_id, similarity in similar_users:
            user = User.query.get(other_user_id)
            if user:
                result.append({
                    'user_id': user.id,
                    'username': user.username,
                    'similarity_score': round(similarity, 3)
                })
        
        return jsonify({'similar_users': result})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@recommendation_bp.route('/user-preferences', methods=['GET'])
@jwt_required()
def get_user_preferences():
    """
    Analyse les préférences de l'utilisateur connecté
    """
    user_id = get_jwt_identity()
    
    try:
        preferences = recommendation_service.get_user_preferences(user_id)
        
        # Formater la réponse
        formatted_preferences = {
            'top_genres': dict(sorted(preferences['genres'].items(), 
                                key=lambda x: x[1], reverse=True)[:10]),
            'favorite_directors': dict(sorted(preferences['directors'].items(), 
                                            key=lambda x: x[1], reverse=True)[:5]),
            'keyword_count': len(set(preferences['keywords']))
        }
        
        return jsonify({
            'preferences': formatted_preferences,
            'total_interactions': len(recommendation_service.build_user_movie_matrix().get(user_id, {}))
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#ceci marche
@recommendation_bp.route('/popular', methods=['GET'])
def get_popular_movies():
    """
    Récupère les films populaires basés sur les interactions
    """
    limit = int(request.args.get('limit', 10))
    
    try:
        # Calculer la popularité basée sur les ratings, likes et reviews
        from sqlalchemy import func
        
        # Sous-requête pour les ratings moyens
        avg_ratings = db.session.query(
            Rating.movie_id,
            func.avg(Rating.rating).label('avg_rating'),
            func.count(Rating.id).label('rating_count')
        ).group_by(Rating.movie_id).subquery()
        
        # Sous-requête pour les likes
        like_counts = db.session.query(
            Like.movie_id,
            func.count(Like.id).label('like_count')
        ).group_by(Like.movie_id).subquery()
        
        # Sous-requête pour les reviews
        review_counts = db.session.query(
            Review.movie_id,
            func.count(Review.id).label('review_count')
        ).group_by(Review.movie_id).subquery()
        
        # Requête principale pour obtenir les films populaires
        popular_movies = db.session.query(Movie)\
            .outerjoin(avg_ratings, Movie.id == avg_ratings.c.movie_id)\
            .outerjoin(like_counts, Movie.id == like_counts.c.movie_id)\
            .outerjoin(review_counts, Movie.id == review_counts.c.movie_id)\
            .add_columns(
                avg_ratings.c.avg_rating,
                avg_ratings.c.rating_count,
                like_counts.c.like_count,
                review_counts.c.review_count
            )\
            .order_by(
                (func.coalesce(avg_ratings.c.avg_rating, 0) * 0.4 +
                 func.coalesce(like_counts.c.like_count, 0) * 0.3 +
                 func.coalesce(review_counts.c.review_count, 0) * 0.3).desc()
            )\
            .limit(limit)\
            .all()
        
        result = []
        for movie_data in popular_movies:
            movie = movie_data[0]  # L'objet Movie
            result.append({
                'id': movie.id,
                'title': movie.title,
                'release_year': movie.release_year,
                'rating': movie.rating,
                'description': movie.description,
                'poster_url': movie.poster_url,
                "video_path":movie.video_file_path,
                'avg_user_rating': round(movie_data[1] or 0, 2),
                'rating_count': movie_data[2] or 0,
                'like_count': movie_data[3] or 0,
                'review_count': movie_data[4] or 0,
                'director': movie.director.name if movie.director else None,
                'genres': [genre.name for genre in movie.genres]
            })
        
        return jsonify({
            'popular_movies': result,
            'total': len(result)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

#ceci marche
@recommendation_bp.route('/by-genre/<genre_name>', methods=['GET'])
def get_recommendations_by_genre(genre_name):
    """
    Recommandations basées sur un genre spécifique
    """
    limit = int(request.args.get('limit', 10))
    
    try:
        from app.models import Genre
        
        # Trouver le genre
        genre = Genre.query.filter_by(name=genre_name).first()
        if not genre:
            return jsonify({'error': 'Genre non trouvé'}), 404
        
        # Obtenir les films du genre triés par popularité
        movies_in_genre = []
        for movie in genre.movies:
            score = 0
            # Calculer un score basé sur les interactions
            ratings = Rating.query.filter_by(movie_id=movie.id).all()
            likes = Like.query.filter_by(movie_id=movie.id).count()
            reviews = Review.query.filter_by(movie_id=movie.id).count()
            
            if ratings:
                avg_rating = sum(r.rating for r in ratings if r.rating) / len(ratings)
                score = (avg_rating / 5.0) * 0.6 + (likes * 0.02) + (reviews * 0.01)
            else:
                score = (likes * 0.02) + (reviews * 0.01)
            
            movies_in_genre.append((movie, score))
        
        # Trier par score décroissant
        movies_in_genre.sort(key=lambda x: x[1], reverse=True)
        
        result = []
        for movie, score in movies_in_genre[:limit]:
            result.append({
                'id': movie.id,
                'title': movie.title,
                'release_year': movie.release_year,
                'rating': movie.rating,
                'description': movie.description,
                'poster_url': movie.poster_url,
                'popularity_score': round(score, 3),
                'director': movie.director.name if movie.director else None,
                'genres': [g.name for g in movie.genres]
            })
        
        return jsonify({
            'recommendations': result,
            'genre': genre_name,
            'total': len(result)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@recommendation_bp.route('/admin/generate-all', methods=['POST'])
@jwt_required()
def generate_all_recommendations():
    """
    Génère les recommandations pour tous les utilisateurs (admin seulement)
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user or not user.is_admin:
        return jsonify({'error': 'Accès refusé'}), 403
    
    try:
        recommendation_service.generate_recommendations_for_all_users()
        return jsonify({'message': 'Recommandations générées pour tous les utilisateurs'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#ceci marche
@recommendation_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_recommendation_stats():
    """
    Statistiques sur les recommandations de l'utilisateur
    """
    user_id = get_jwt_identity()
    
    try:
        stats = {
            'total_ratings': Rating.query.filter_by(user_id=user_id).count(),
            'total_likes': Like.query.filter_by(user_id=user_id).count(),
            'total_reviews': Review.query.filter_by(user_id=user_id).count(),
            'avg_rating_given': 0
        }
        
        # Calculer la note moyenne donnée par l'utilisateur
        user_ratings = Rating.query.filter_by(user_id=user_id).all()
        if user_ratings:
            total_rating = sum(r.rating for r in user_ratings if r.rating)
            stats['avg_rating_given'] = round(total_rating / len(user_ratings), 2)
        
        return jsonify({'stats': stats})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    


@recommendation_bp.route('/test', methods=['GET'])
@jwt_required()
def test_auth():
    user_id = get_jwt_identity()
    return jsonify({"message": "Test réussi", "user_id": user_id})
# service/recommendation_service.py

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict
from app.models import User, Movie, Rating, Review, Like, Recommendation
from app.extensions import db
import pandas as pd

class RecommendationService:
    
    def __init__(self):
        self.user_similarity_matrix = None
        self.movie_similarity_matrix = None
    
    def calculate_user_score(self, user_id, movie_id):
        score = 0.0

        rating = Rating.query.filter_by(user_id=user_id, movie_id=movie_id).first()
        if rating and rating.rating:
            score += (rating.rating / 5.0) * 0.4

        review = Review.query.filter_by(user_id=user_id, movie_id=movie_id).first()
        if review:
            if review.rating:
                score += (review.rating / 5.0) * 0.3
            else:
                sentiment_score = self.analyze_review_sentiment(review.review_text)
                score += sentiment_score * 0.3

        like = Like.query.filter_by(user_id=user_id, movie_id=movie_id).first()
        if like:
            score += 0.3
        
        return min(score, 1.0)
    
    def analyze_review_sentiment(self, review_text):
        positive_words = ['excellent', 'génial', 'super', 'parfait', 'incroyable', 
                          'fantastique', 'merveilleux', 'brillant', 'magnifique']
        negative_words = ['nul', 'horrible', 'décevant', 'ennuyeux', 'mauvais',
                          'terrible', 'affreux', 'catastrophique']
        
        text_lower = review_text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count + negative_count == 0:
            return 0.5
        
        return positive_count / (positive_count + negative_count)
    
    def build_user_movie_matrix(self):
        users = User.query.all()
        movies = Movie.query.all()
        user_movie_scores = defaultdict(dict)
        
        for user in users:
            for movie in movies:
                score = self.calculate_user_score(user.id, movie.id)
                if score > 0:
                    user_movie_scores[user.id][movie.id] = score
        return user_movie_scores
    
    def collaborative_filtering_user_based(self, target_user_id, n_recommendations=10):
        user_movie_scores = self.build_user_movie_matrix()
        if target_user_id not in user_movie_scores:
            return []
        
        target_user_scores = user_movie_scores[target_user_id]
        similarities = {}
        
        for user_id, scores in user_movie_scores.items():
            if user_id != target_user_id:
                similarity = self.calculate_user_similarity(target_user_scores, scores)
                if similarity > 0:
                    similarities[user_id] = similarity
        
        similar_users = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:20]
        
        movie_scores = defaultdict(float)
        total_similarity = defaultdict(float)
        
        for similar_user_id, similarity in similar_users:
            for movie_id, score in user_movie_scores[similar_user_id].items():
                if movie_id not in target_user_scores:
                    movie_scores[movie_id] += score * similarity
                    total_similarity[movie_id] += similarity
        
        recommendations = []
        for movie_id, total_score in movie_scores.items():
            if total_similarity[movie_id] > 0:
                final_score = total_score / total_similarity[movie_id]
                recommendations.append((movie_id, final_score))
        
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:n_recommendations]
    
    def calculate_user_similarity(self, user1_scores, user2_scores):
        common_movies = set(user1_scores.keys()) & set(user2_scores.keys())
        if len(common_movies) < 2:
            return 0
        
        scores1 = np.array([user1_scores[movie_id] for movie_id in common_movies])
        scores2 = np.array([user2_scores[movie_id] for movie_id in common_movies])
        
        if np.linalg.norm(scores1) == 0 or np.linalg.norm(scores2) == 0:
            return 0
        
        return np.dot(scores1, scores2) / (np.linalg.norm(scores1) * np.linalg.norm(scores2))
    
    def content_based_filtering(self, target_user_id, n_recommendations=10):
        user_preferences = self.get_user_preferences(target_user_id)
        if not user_preferences:
            return []
        
        user_movie_scores = self.build_user_movie_matrix()
        seen_movies = set(user_movie_scores.get(target_user_id, {}).keys())
        
        all_movies = Movie.query.all()
        unseen_movies = [movie for movie in all_movies if movie.id not in seen_movies]
        
        recommendations = []
        for movie in unseen_movies:
            score = self.calculate_content_similarity(user_preferences, movie)
            if score > 0:
                recommendations.append((movie.id, score))
        
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:n_recommendations]
    
    def get_user_preferences(self, user_id):
        preferences = {
            'genres': defaultdict(float),
            'directors': defaultdict(float),
            'keywords': []
        }
        
        user_movie_scores = self.build_user_movie_matrix()
        user_scores = user_movie_scores.get(user_id, {})
        
        for movie_id, score in user_scores.items():
            if score > 0.6:
                movie = Movie.query.get(movie_id)
                if movie:
                    for genre in movie.genres:
                        preferences['genres'][genre.name] += score
                    if movie.director:
                        preferences['directors'][movie.director.name] += score
                    reviews = Review.query.filter_by(movie_id=movie_id).all()
                    for review in reviews:
                        if review.rating and review.rating >= 4:
                            preferences['keywords'].extend(review.review_text.lower().split())
        
        return preferences
    
    def calculate_content_similarity(self, user_preferences, movie):
        score = 0.0
        
        genre_score = 0.0
        total_genre_weight = sum(user_preferences['genres'].values())
        if total_genre_weight > 0:
            for genre in movie.genres:
                if genre.name in user_preferences['genres']:
                    genre_score += user_preferences['genres'][genre.name] / total_genre_weight
        score += genre_score * 0.5
        
        if movie.director and movie.director.name in user_preferences['directors']:
            director_score = user_preferences['directors'][movie.director.name]
            total_director_weight = sum(user_preferences['directors'].values())
            score += (director_score / total_director_weight) * 0.3
        
        if movie.description and user_preferences['keywords']:
            keyword_score = self.calculate_keyword_similarity(
                movie.description, 
                user_preferences['keywords']
            )
            score += keyword_score * 0.2
        
        return min(score, 1.0)
    
    def calculate_keyword_similarity(self, description, user_keywords):
        corpus = [' '.join(user_keywords), description]
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(corpus)
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
        return similarity[0][0]  # entre 0 et 1
    
    def hybrid_recommendation(self, user_id, n_recommendations=10):
        collaborative_recs = self.collaborative_filtering_user_based(user_id, n_recommendations * 2)
        content_recs = self.content_based_filtering(user_id, n_recommendations * 2)
        
        combined_scores = defaultdict(float)
        
        for movie_id, score in collaborative_recs:
            combined_scores[movie_id] += score * 0.7
        
        for movie_id, score in content_recs:
            combined_scores[movie_id] += score * 0.3
        
        final_recommendations = sorted(
            combined_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return final_recommendations[:n_recommendations]
    
    def save_recommendations_to_db(self, user_id, recommendations):
        Recommendation.query.filter_by(user_id=user_id).delete()
        for movie_id, score in recommendations:
            recommendation = Recommendation(
                user_id=user_id,
                movie_id=movie_id,
                score=score
            )
            db.session.add(recommendation)
        db.session.commit()
    
    def generate_recommendations_for_user(self, user_id, method='hybrid', n_recommendations=10):
        if method == 'collaborative':
            recommendations = self.collaborative_filtering_user_based(user_id, n_recommendations)
        elif method == 'content':
            recommendations = self.content_based_filtering(user_id, n_recommendations)
        else:
            recommendations = self.hybrid_recommendation(user_id, n_recommendations)
        
        self.save_recommendations_to_db(user_id, recommendations)
        return recommendations
    
    def generate_recommendations_for_all_users(self):
        users = User.query.all()
        for user in users:
            try:
                self.generate_recommendations_for_user(user.id)
                print(f"Recommandations générées pour l'utilisateur {user.id}")
            except Exception as e:
                print(f"Erreur pour l'utilisateur {user.id}: {e}")
    
    def get_user_recommendations(self, user_id, limit=10):
        recommendations = Recommendation.query.filter_by(user_id=user_id)\
            .order_by(Recommendation.score.desc())\
            .limit(limit).all()
        return [(rec.movie_id, rec.score) for rec in recommendations]

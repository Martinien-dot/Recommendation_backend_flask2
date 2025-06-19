from app.models.movie import Movie
from app.models.review import Review
from app.extensions import db


def update_movie_rating(movie_id):
    reviews = Review.query.filter_by(movie_id=movie_id).all()
    movie = Movie.query.get(movie_id)

    if not movie:
        return

    # Si des avis existent
    if reviews:
        # Calcule la moyenne des notes
        average_rating = sum([r.rating for r in reviews if r.rating is not None]) / len(reviews)
        movie.rating = round(average_rating, 2)  # arrondi à 2 décimales
    else:
        movie.rating = None  # Aucun avis = pas de note

    db.session.commit()
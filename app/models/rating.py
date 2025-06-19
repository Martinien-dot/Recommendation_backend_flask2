# Modèle Rating (Note)
# Ce modèle représente les notes attribuées par les utilisateurs aux films.
from app.extensions import db

class Rating(db.Model):
    __tablename__ = 'ratings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    rating = db.Column(db.Float, nullable=True)  # Note attribuée par l'utilisateur (ex : 4.5)

    # Relations (facultatif mais recommandé)
    user = db.relationship('User', backref=db.backref('ratings', lazy=True))
    movie = db.relationship('Movie', backref=db.backref('ratings', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'movie_id', name='unique_user_movie_rating'),
    )

# Modèle Favorite (Favoris)
# Ce modèle permet aux utilisateurs de marquer des films comme favoris.
from app.extensions import db
class Favorite(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relations
    user = db.relationship('User', backref=db.backref('favorites', lazy=True))
    movie = db.relationship('Movie', backref=db.backref('favorites', lazy=True))
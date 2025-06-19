# Modèle Watchlist (Liste de souhaits)
# Ce modèle permet aux utilisateurs de créer des listes de films à regarder plus tard.
from app.extensions import db
class Watchlist(db.Model):
    __tablename__ = 'watchlists'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relations
    user = db.relationship('User', backref=db.backref('watchlists', lazy=True))
    movie = db.relationship('Movie', backref=db.backref('watchlists', lazy=True))
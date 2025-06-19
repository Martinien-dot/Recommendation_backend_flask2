# Modèle Recommendation (Recommandation)
# Ce modèle stocke les recommandations générées par votre système de recommandation.
from app.extensions import db

class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)  # Score de recommandation
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relations
    user = db.relationship('User', backref=db.backref('recommendations', lazy=True))
    movie = db.relationship('Movie', backref=db.backref('recommendations', lazy=True))
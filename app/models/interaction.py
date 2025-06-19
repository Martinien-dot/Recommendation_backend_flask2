# Modèle Interaction (Interaction Utilisateur-Film)
# Ce modèle enregistre les interactions des utilisateurs avec les films.
from app.extensions import db
class Interaction(db.Model):
    __tablename__ = 'interactions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)
    interaction_type = db.Column(db.String(50), nullable=False)  # Ex: 'viewed', 'wishlist'
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relations
    user = db.relationship('User', backref=db.backref('interactions', lazy=True))
    movie = db.relationship('Movie', backref=db.backref('interactions', lazy=True))
# Modèle Director (Réalisateur)
# Ce modèle stocke des informations sur les réalisateurs.
from app.extensions import db
class Director(db.Model):
    __tablename__ = 'directors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text)  # Biographie du réalisateur

    # Relation one-to-many avec Movie
    movies = db.relationship('Movie', backref=db.backref('director', lazy=True))
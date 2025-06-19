# Modèle Movie (Film)
# Ce modèle représente les films dans votre base de données.
from app.extensions import db
class Movie(db.Model):
    __tablename__ = 'movies'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    release_year = db.Column(db.Integer)
    rating = db.Column(db.Float)  # Note moyenne du film
    description = db.Column(db.Text)  # Description du film
    poster_url = db.Column(db.String(500))  # URL de l'affiche du film
    video_file_path = db.Column(db.String(500))  # Chemin du fichier vidéo local


    # Relation Many-to-One avec Director (un film a un seul réalisateur)
    director_id = db.Column(db.Integer, db.ForeignKey('directors.id'), nullable=False)


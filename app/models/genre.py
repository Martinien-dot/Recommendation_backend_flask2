# Modèle Genre (Genre de film)
# Ce modèle représente les genres de films.
from app.extensions import db
class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    # Relation many-to-many avec Movie
    movies = db.relationship('Movie', secondary='movie_genres', backref=db.backref('genres', lazy=True))
    

# Table d'association pour la relation many-to-many entre Movie et Genre
movie_genres = db.Table('movie_genres',
    db.Column('movie_id', db.Integer, db.ForeignKey('movies.id'), primary_key=True),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id'), primary_key=True)
)
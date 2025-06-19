# Modèle Actor (Acteur)
# Ce modèle stocke des informations sur les acteurs.
from app.extensions import db
class Actor(db.Model):
    __tablename__ = 'actors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text)  # Biographie de l'acteur

    # Relation many-to-many avec Movie
    movies = db.relationship('Movie', secondary='movie_actors', backref=db.backref('actors', lazy=True))
# Table d'association pour la relation many-to-many entre Movie et Actor
movie_actors = db.Table('movie_actors',
    db.Column('movie_id', db.Integer, db.ForeignKey('movies.id'), primary_key=True),
    db.Column('actor_id', db.Integer, db.ForeignKey('actors.id'), primary_key=True)
)
# Modèle Like (Aime)
# Ce modèle représente les likes attribués par les utilisateurs aux films.

from app.extensions import db

class Like(db.Model):
    __tablename__ = 'likes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    movie_id = db.Column(db.Integer, db.ForeignKey('movies.id'), nullable=False)

    # Relations
    user = db.relationship('User', backref=db.backref('likes', lazy=True))
    movie = db.relationship('Movie', backref=db.backref('likes', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'movie_id', name='unique_user_movie_like'),
    )

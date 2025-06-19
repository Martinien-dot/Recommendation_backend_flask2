# Modèle Role (Rôle)
# Ce modèle représente les différents rôles que les utilisateurs peuvent avoir.
from app.extensions import db
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    # Relation avec User
    users = db.relationship('User', backref='role', lazy=True)
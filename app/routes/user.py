from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash

user_bp = Blueprint('user', __name__, url_prefix='/users')

@user_bp.route('/', methods=['GET'])
def get_all_users():
    """Récupérer tous les utilisateurs"""
    users = User.query.all()
    return jsonify([{"id": u.id, "username": u.username, "email": u.email} for u in users])

@user_bp.route('/<int:id>', methods=['GET'])
def get_user(id):
    """Récupérer un utilisateur spécifique"""
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    return jsonify({"id": user.id, "username": user.username, "email": user.email})

@user_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_user(id):
    """Mettre à jour un utilisateur (seulement son propre compte)"""
    current_user_id = get_jwt_identity()
    if current_user_id != id:
        return jsonify({"error": "Action non autorisée"}), 403

    user = User.query.get(id)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    data = request.get_json()
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user and existing_user.id != id:
            return jsonify({"error": "Cet email est déjà utilisé"}), 400
        user.email = data['email']
    if 'password' in data:
        user.password = generate_password_hash(data['password'])

    db.session.commit()
    return jsonify({"message": "Informations mises à jour avec succès"})

@user_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_user(id):
    """Supprimer un utilisateur (seulement son propre compte)"""
    current_user_id = get_jwt_identity()
    if current_user_id != id:
        return jsonify({"error": "Action non autorisée"}), 403

    user = User.query.get(id)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Utilisateur supprimé avec succès"})

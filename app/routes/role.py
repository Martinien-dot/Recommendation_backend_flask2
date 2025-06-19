from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.user import User

role_bp = Blueprint('role', __name__, url_prefix='/roles')

@role_bp.route('/assign', methods=['POST'])
@jwt_required()
def assign_role():
    """Assigner un rôle à un utilisateur (Admin uniquement)"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)

    if not current_user or current_user.role != 'admin':
        return jsonify({"error": "Accès refusé, admin requis"}), 403

    data = request.get_json()
    user_id = data.get('user_id')
    new_role = data.get('role')

    if not user_id or not new_role:
        return jsonify({"error": "ID utilisateur et rôle requis"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 404

    user.role = new_role
    db.session.commit()

    return jsonify({"message": f"Rôle mis à jour : {user.username} → {new_role}"}), 200

@role_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_role(user_id):
    """Obtenir le rôle d’un utilisateur"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilisateur introuvable"}), 404

    return jsonify({"user_id": user.id, "username": user.username, "role": user.role})

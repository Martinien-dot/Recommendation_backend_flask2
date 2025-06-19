from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from typing import List, Dict, Any, Tuple, Union, Optional

user_bp = Blueprint('user', __name__, url_prefix='/users')

@user_bp.route('/', methods=['GET'])
def get_all_users() -> List[Dict[str, Union[int, str]]]:
    """
    Récupère tous les utilisateurs (sans informations sensibles)
    ---
    tags:
      - Utilisateurs
    responses:
      200:
        description: Liste de tous les utilisateurs
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: ID de l'utilisateur
              username:
                type: string
                description: Nom d'utilisateur
              email:
                type: string
                description: Adresse email
    security: []  # Aucune authentification requise
    """
    users = User.query.all()
    return jsonify([{"id": u.id, "username": u.username, "email": u.email} for u in users])

@user_bp.route('/<int:id>', methods=['GET'])
def get_user(id: int) -> Union[Dict[str, Union[int, str]], Tuple[Dict[str, str], int]]:
    """
    Récupère un utilisateur spécifique
    ---
    tags:
      - Utilisateurs
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de l'utilisateur
    responses:
      200:
        description: Détails de l'utilisateur
        schema:
          type: object
          properties:
            id:
              type: integer
            username:
              type: string
            email:
              type: string
      404:
        description: Utilisateur non trouvé
    security: []  # Aucune authentification requise
    """
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404
    return jsonify({"id": user.id, "username": user.username, "email": user.email})

@user_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
def update_user(id: int) -> Union[Dict[str, str], Tuple[Dict[str, str], int]]:
    """
    Met à jour les informations d'un utilisateur (uniquement son propre compte)
    ---
    tags:
      - Utilisateurs
    security:
      - JWT: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de l'utilisateur à mettre à jour
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: nouveau_username
            email:
              type: string
              example: nouveau@email.com
            password:
              type: string
              example: nouveauMotDePasse
    responses:
      200:
        description: Utilisateur mis à jour
      400:
        description: Email déjà utilisé
      403:
        description: Action non autorisée
      404:
        description: Utilisateur non trouvé
    """
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
def delete_user(id: int) -> Union[Dict[str, str], Tuple[Dict[str, str], int]]:
    """
    Supprime un utilisateur (uniquement son propre compte)
    ---
    tags:
      - Utilisateurs
    security:
      - JWT: []
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID de l'utilisateur à supprimer
    responses:
      200:
        description: Utilisateur supprimé
      403:
        description: Action non autorisée
      404:
        description: Utilisateur non trouvé
    """
    current_user_id = get_jwt_identity()
    if current_user_id != id:
        return jsonify({"error": "Action non autorisée"}), 403

    user = User.query.get(id)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Utilisateur supprimé avec succès"})
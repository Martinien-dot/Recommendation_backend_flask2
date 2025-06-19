from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Dict, Tuple, Union, Optional

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/check-email', methods=['GET'])
def check_email() -> Tuple[Dict[str, Union[bool, str]], int]:
    """
    Vérifie si un email existe déjà dans la base de données
    ---
    tags:
      - Authentification
    parameters:
      - name: email
        in: query
        type: string
        required: true
        description: Email à vérifier
    responses:
      200:
        description: Résultat de la vérification
        schema:
          type: object
          properties:
            exists:
              type: boolean
              description: Indique si l'email existe
            message:
              type: string
              description: Message détaillé
      400:
        description: Paramètre email manquant
    """
    email = request.args.get('email')
    
    if not email:
        return jsonify({"error": "Paramètre email requis"}), 400
    
    user_exists = User.query.filter_by(email=email).first() is not None
    
    if user_exists:
        return jsonify({
            "exists": True,
            "message": "Cet email est déjà utilisé"
        }), 200
    else:
        return jsonify({
            "exists": False,
            "message": "Email disponible"
        }), 200

@auth_bp.route('/register', methods=['POST'])
def register() -> Tuple[Dict[str, Union[str, int]], int]:
    """
    Crée un nouveau compte utilisateur
    ---
    tags:
      - Authentification
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - email
            - password
          properties:
            username:
              type: string
              example: martinien
            email:
              type: string
              example: martiniengaba@gmail.com
            password:
              type: string
              example: monMotDePasse
    responses:
      201:
        description: Utilisateur créé avec succès
        schema:
          type: object
          properties:
            message:
              type: string
            id:
              type: integer
      400:
        description: Données invalides ou email déjà utilisé
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données JSON manquantes"}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "Tous les champs sont requis"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Cet email est déjà utilisé"}), 400

    user = User(username=username, email=email)
    user.set_password(password)
    user.role_id = 1

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Utilisateur créé avec succès", "id": user.id}), 201

@auth_bp.route('/login', methods=['POST'])
def login() -> Tuple[Dict[str, Union[str, int]], int]:
    """
    Authentifie un utilisateur et retourne un token JWT
    ---
    tags:
      - Authentification
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: martiniengaba@gmail.com
            password:
              type: string
              example: monMotDePasse
    responses:
      200:
        description: Connexion réussie
        schema:
          type: object
          properties:
            message:
              type: string
            token:
              type: string
              description: JWT token pour les requêtes authentifiées
            id:
              type: integer
              description: ID de l'utilisateur
      400:
        description: Données manquantes
      401:
        description: Identifiants invalides
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données JSON manquantes"}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email et mot de passe requis"}), 400
    
    user: User = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Identifiants invalides"}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"message": "Connexion réussie", "token": access_token, "id": user.id}), 200

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected() -> Tuple[Dict[str, Union[str, int]], int]:
    """
    Route protégée nécessitant un token JWT valide
    ---
    tags:
      - Authentification
    security:
      - JWT: []
    responses:
      200:
        description: Accès autorisé
        schema:
          type: object
          properties:
            message:
              type: string
            user_id:
              type: integer
      401:
        description: Token manquant ou invalide
    """
    current_user_id = get_jwt_identity()
    return jsonify({"message": "Accès autorisé", "user_id": current_user_id}), 200

@auth_bp.route('/update_profile', methods=['PUT'])
@jwt_required()
def update_profile() -> Tuple[Dict[str, str], int]:
    """
    Met à jour le profil de l'utilisateur connecté
    ---
    tags:
      - Authentification
    security:
      - JWT: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              example: nouveau_nom
            email:
              type: string
              example: nouveau@email.com
            password:
              type: string
              example: nouveauMotDePasse
    responses:
      200:
        description: Profil mis à jour
      400:
        description: Données invalides ou email déjà utilisé
      401:
        description: Non autorisé
      404:
        description: Utilisateur non trouvé
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données JSON manquantes"}), 400

    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    new_username = data.get('username', user.username)
    new_email = data.get('email', user.email)
    new_password = data.get('password')

    if new_email != user.email and User.query.filter_by(email=new_email).first():
        return jsonify({"error": "Cet email est déjà utilisé"}), 400

    user.username = new_username
    user.email = new_email

    if new_password:
        user.set_password(new_password)

    db.session.commit()

    return jsonify({"message": "Profil mis à jour avec succès"}), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout() -> Tuple[Dict[str, str], int]:
    """
    Déconnecte l'utilisateur (fonctionnalité de base)
    ---
    tags:
      - Authentification
    security:
      - JWT: []
    responses:
      200:
        description: Déconnexion réussie
      401:
        description: Non autorisé
    """
    return jsonify({"message": "Déconnexion réussie"}), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user() -> Tuple[Dict[str, Union[str, int]], int]:
    """
    Récupère les informations de l'utilisateur connecté
    ---
    tags:
      - Authentification
    security:
      - JWT: []
    responses:
      200:
        description: Informations utilisateur
        schema:
          type: object
          properties:
            id:
              type: integer
            username:
              type: string
            email:
              type: string
            role_id:
              type: integer
      401:
        description: Non autorisé
      404:
        description: Utilisateur non trouvé
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role_id": user.role_id
    }), 200
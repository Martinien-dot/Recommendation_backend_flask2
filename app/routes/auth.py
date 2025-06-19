from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.user import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash


auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
"""exemple d'utilisateur:  {
  "username": "martinien",
  "email": "martiniengaba@gmail.com",
  "password": "monMotDePasse"
}"""

@auth_bp.route('/check-email', methods=['GET'])
def check_email():
    """Vérifier si un email existe déjà"""
    email = request.args.get('email')
    
    if not email:
        return jsonify({"error": "Paramètre email requis"}), 400
    
    # Pour des raisons de sécurité, nous ne voulons pas révéler si un email existe
    # Nous retournons toujours exists: false mais avec un message différent
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
def register():
    """Créer un utilisateur"""
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
def login():
    """Connexion et génération d'un token JWT"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données JSON manquantes"}), 400

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email et mot de passe requis"}), 400
    
    user:User = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Identifiants invalides"}), 401

    access_token = create_access_token(identity=str(user.id))
    return jsonify({"message": "Connexion réussie", "token": access_token, "id":user.id}), 200

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    """Route protégée pour tester l'authentification"""
    current_user_id = get_jwt_identity()
    return jsonify({"message": "Accès autorisé", "user_id": current_user_id}), 200



@auth_bp.route('/update_profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Mettre à jour le profil de l'utilisateur connecté"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Données JSON manquantes"}), 400

    current_user_id = get_jwt_identity()  # Récupérer l'ID utilisateur à partir du token
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    new_username = data.get('username', user.username)
    new_email = data.get('email', user.email)
    new_password = data.get('password')

    # Vérifier si l'email est déjà utilisé par un autre utilisateur
    if new_email != user.email and User.query.filter_by(email=new_email).first():
        return jsonify({"error": "Cet email est déjà utilisé"}), 400

    # Mise à jour des informations
    user.username = new_username
    user.email = new_email

    if new_password:
        user.set_password(new_password)

    db.session.commit()

    return jsonify({"message": "Profil mis à jour avec succès"}), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Déconnexion (optionnel, si on utilise une liste noire de tokens)"""
    return jsonify({"message": "Déconnexion réussie"}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Récupérer les infos de l'utilisateur connecté via le token JWT"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "Utilisateur non trouvé"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role_id": user.role_id
    })
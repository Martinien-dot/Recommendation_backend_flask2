from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_jwt_extended import JWTManager  # Ajout de JWT
from flask_cors import CORS  # Ajout de CORS

# Initialisation des extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
jwt = JWTManager()  # Ajout de JWT
cors = CORS(
    resources={r"/*": {"origins": ["http://localhost:3000", "http://localhost:64110"]}},
    supports_credentials=True
)  # Ajout de CORS

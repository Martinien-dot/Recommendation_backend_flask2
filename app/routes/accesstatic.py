from flask import Flask, send_from_directory
from flask import Blueprint, request, jsonify
import os

access_bp = Blueprint('access_movie', __name__, url_prefix='/')

# Route pour servir les images (posters)
@access_bp.route('/static/posters/<path:filename>')
def serve_posters(filename):
    # Spécifier le chemin absolu vers le dossier static/posters
    posters_folder = os.path.join(os.getcwd(), 'static', 'posters')
    return send_from_directory(posters_folder, filename)

# Route pour servir les vidéos
@access_bp.route('/static/videos/<path:filename>')
def serve_videos(filename):
    # Spécifier le chemin absolu vers le dossier static/videos
    videos_folder = os.path.join(os.getcwd(), 'static', 'videos')
    return send_from_directory(videos_folder, filename)


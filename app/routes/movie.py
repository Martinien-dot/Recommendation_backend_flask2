from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.actor import Actor
from app.models.director import Director
from app.models.genre import Genre
from app.models.movie import Movie
from typing import List, Dict, Any, Tuple, Union, Optional

movie_bp = Blueprint('movie', __name__, url_prefix='/movies')

@movie_bp.route('/search', methods=['GET'])
def search_movies() -> Union[Dict[str, Any], Tuple[Dict[str, str], int]]:
    """
    Recherche des films selon différents critères
    ---
    tags:
      - Films
    parameters:
      - name: q
        in: query
        type: string
        description: Terme de recherche (titre ou description)
      - name: genre
        in: query
        type: string
        description: Nom du genre à filtrer
      - name: director
        in: query
        type: string
        description: Nom du réalisateur à filtrer
      - name: actor
        in: query
        type: string
        description: Nom de l'acteur à filtrer
    responses:
      200:
        description: Liste des films correspondants
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              title:
                type: string
              poster_url:
                type: string
              video_path:
                type: string
              release_year:
                type: integer
              rating:
                type: number
              director:
                type: string
              genres:
                type: array
                items:
                  type: string
              actors:
                type: array
                items:
                  type: string
      500:
        description: Erreur serveur
    """
    try:
        query = request.args.get('q', '').strip().lower()
        genre = request.args.get('genre', '').strip().lower()
        director = request.args.get('director', '').strip().lower()
        actor = request.args.get('actor', '').strip().lower()
        
        movies_query = Movie.query
        
        if query:
            movies_query = movies_query.filter(
                db.or_(
                    Movie.title.ilike(f'%{query}%'),
                    Movie.description.ilike(f'%{query}%')
                )
            )
        
        if genre:
            movies_query = movies_query.join(Movie.genres).filter(
                db.func.lower(Genre.name).ilike(f'%{genre}%')
            )
        
        if director:
            movies_query = movies_query.join(Movie.director).filter(
                db.func.lower(Director.name).ilike(f'%{director}%')
            )
        
        if actor:
            movies_query = movies_query.join(Movie.actors).filter(
                db.func.lower(Actor.name).ilike(f'%{actor}%')
            )
        
        movies = movies_query.distinct().all()
        
        results = []
        for movie in movies:
            results.append({
                "id": movie.id,
                "title": movie.title,
                "poster_url": movie.poster_url,
                "video_path": movie.video_file_path,
                "release_year": movie.release_year,
                "rating": movie.rating,
                "director": movie.director.name if movie.director else None,
                "genres": [genre.name for genre in movie.genres],
                "actors": [actor.name for actor in movie.actors]
            })
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@movie_bp.route('/', methods=['GET'])
def get_all_movies() -> List[Dict[str, Union[int, str, None]]]:
    """
    Récupère tous les films
    ---
    tags:
      - Films
    responses:
      200:
        description: Liste de tous les films
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              title:
                type: string
              poster_url:
                type: string
              director_id:
                type: integer
              video_path:
                type: string
    """
    movies = Movie.query.all()
    return jsonify([{
        "id": m.id, 
        "title": m.title, 
        "poster_url": m.poster_url, 
        "director_id": m.director_id, 
        "video_path": m.video_file_path
    } for m in movies])

@movie_bp.route('/<int:id>', methods=['GET'])
def get_movie(id: int) -> Union[Dict[str, Union[int, str, None]], Tuple[Dict[str, str], int]]:
    """
    Récupère un film spécifique
    ---
    tags:
      - Films
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID du film
    responses:
      200:
        description: Détails du film
        schema:
          type: object
          properties:
            id:
              type: integer
            title:
              type: string
            poster_url:
              type: string
            director_id:
              type: integer
            video_path:
              type: string
      404:
        description: Film non trouvé
    """
    movie = Movie.query.get(id)
    if not movie:
        return jsonify({"error": "Film non trouvé"}), 404
    return jsonify({
        "id": movie.id, 
        "title": movie.title, 
        "poster_url": movie.poster_url, 
        "director_id": movie.director_id, 
        "video_path": movie.video_file_path
    })

@movie_bp.route('/', methods=['POST'])
def create_movie() -> Tuple[Dict[str, Union[str, int]], int]:
    """
    Crée un nouveau film
    ---
    tags:
      - Films
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - title
            - genre_id
            - director_id
          properties:
            title:
              type: string
              example: Inception
            genre_id:
              type: integer
              example: 1
            director_id:
              type: integer
              example: 1
    responses:
      201:
        description: Film créé avec succès
        schema:
          type: object
          properties:
            message:
              type: string
            id:
              type: integer
      400:
        description: Données manquantes ou invalides
    """
    data = request.get_json()
    title = data.get('title')
    genre_id = data.get('genre_id')
    director_id = data.get('director_id')

    if not title or not genre_id or not director_id:
        return jsonify({"error": "Les champs title, genre_id et director_id sont requis"}), 400

    movie = Movie(title=title, genre_id=genre_id, director_id=director_id)
    db.session.add(movie)
    db.session.commit()
    
    return jsonify({"message": "Film ajouté avec succès", "id": movie.id}), 201

@movie_bp.route('/<int:id>', methods=['PUT'])
def update_movie(id: int) -> Union[Dict[str, str], Tuple[Dict[str, str], int]]:
    """
    Met à jour un film existant
    ---
    tags:
      - Films
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID du film à mettre à jour
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: Nouveau titre
            genre_id:
              type: integer
              example: 2
            director_id:
              type: integer
              example: 3
    responses:
      200:
        description: Film mis à jour
      404:
        description: Film non trouvé
    """
    movie = Movie.query.get(id)
    if not movie:
        return jsonify({"error": "Film non trouvé"}), 404

    data = request.get_json()
    movie.title = data.get('title', movie.title)
    movie.genre_id = data.get('genre_id', movie.genre_id)
    movie.director_id = data.get('director_id', movie.director_id)

    db.session.commit()
    return jsonify({"message": "Film mis à jour avec succès"})

@movie_bp.route('/<int:id>', methods=['DELETE'])
def delete_movie(id: int) -> Union[Dict[str, str], Tuple[Dict[str, str], int]]:
    """
    Supprime un film
    ---
    tags:
      - Films
    parameters:
      - name: id
        in: path
        type: integer
        required: true
        description: ID du film à supprimer
    responses:
      200:
        description: Film supprimé
      404:
        description: Film non trouvé
    """
    movie = Movie.query.get(id)
    if not movie:
        return jsonify({"error": "Film non trouvé"}), 404

    db.session.delete(movie)
    db.session.commit()
    return jsonify({"message": "Film supprimé avec succès"})

@movie_bp.route('/full', methods=['POST'])
def create_full_movie() -> Tuple[Dict[str, Union[str, int]], int]:
    """
    Crée un film complet avec tous les détails (y compris upload de fichiers)
    ---
    tags:
      - Films
    consumes:
      - multipart/form-data
    parameters:
      - name: title
        in: formData
        type: string
        required: true
      - name: release_year
        in: formData
        type: integer
      - name: rating
        in: formData
        type: number
      - name: description
        in: formData
        type: string
      - name: director
        in: formData
        type: string
        required: true
      - name: actors
        in: formData
        type: array
        items:
          type: string
      - name: genres
        in: formData
        type: array
        items:
          type: string
      - name: poster
        in: formData
        type: file
        description: Affiche du film
      - name: video
        in: formData
        type: file
        description: Fichier vidéo du film
    responses:
      201:
        description: Film créé avec succès
        schema:
          type: object
          properties:
            message:
              type: string
            id:
              type: integer
      400:
        description: Données manquantes ou invalides
      500:
        description: Erreur serveur
    """
    try:
        from werkzeug.utils import secure_filename
        import os

        title = request.form.get('title')
        release_year = request.form.get('release_year')
        rating = request.form.get('rating')
        description = request.form.get('description')
        director_name = request.form.get('director')
        actor_names = request.form.getlist('actors')
        genre_names = request.form.getlist('genres')

        if not title or not director_name:
            return jsonify({"error": "Les champs title et director sont requis"}), 400

        # Upload de l'affiche
        poster_file = request.files.get('poster')
        poster_url = None
        if poster_file:
            folder = 'static/posters'
            os.makedirs(folder, exist_ok=True)
            filename = secure_filename(poster_file.filename)
            poster_path = os.path.join(folder, filename)
            poster_file.save(poster_path)
            poster_url = f'/static/posters/{filename}'

        # Upload de la vidéo
        video_file = request.files.get('video')
        video_path = None
        if video_file:
            video_folder = 'static/videos'
            os.makedirs(video_folder, exist_ok=True)
            video_filename = secure_filename(video_file.filename)
            video_full_path = os.path.join(video_folder, video_filename)
            video_file.save(video_full_path)
            video_path = f'/static/videos/{video_filename}'

        # Réalisateur
        director_key = director_name.replace(" ", "").upper()
        director = Director.query.filter(
            db.func.replace(db.func.upper(Director.name), " ", "") == director_key
        ).first()
        if not director:
            director = Director(name=director_name)
            db.session.add(director)

        # Film
        movie = Movie(
            title=title,
            release_year=int(release_year) if release_year else None,
            rating=float(rating) if rating else None,
            description=description,
            poster_url=poster_url,
            video_file_path=video_path,
            director=director
        )

        # Acteurs
        for actor_name in actor_names:
            key = actor_name.replace(" ", "").upper()
            actor = Actor.query.filter(
                db.func.replace(db.func.upper(Actor.name), " ", "") == key
            ).first()
            if not actor:
                actor = Actor(name=actor_name)
                db.session.add(actor)
            movie.actors.append(actor)

        # Genres
        for genre_name in genre_names:
            key = genre_name.replace(" ", "").upper()
            genre = Genre.query.filter(
                db.func.replace(db.func.upper(Genre.name), " ", "") == key
            ).first()
            if not genre:
                genre = Genre(name=genre_name)
                db.session.add(genre)
            movie.genres.append(genre)

        db.session.add(movie)
        db.session.commit()

        return jsonify({"message": "Film complet ajouté avec succès", "id": movie.id}), 201

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erreur interne: {str(e)}"}), 500
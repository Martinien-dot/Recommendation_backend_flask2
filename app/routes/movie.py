from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.actor import Actor
from app.models.director import Director
from app.models.genre import Genre
from app.models.movie import Movie

movie_bp = Blueprint('movie', __name__, url_prefix='/movies')

@movie_bp.route('/search', methods=['GET'])
def search_movies():
    """Rechercher des films selon différents critères"""
    try:
        # Récupérer les paramètres de recherche
        query = request.args.get('q', '').strip().lower()
        genre = request.args.get('genre', '').strip().lower()
        director = request.args.get('director', '').strip().lower()
        actor = request.args.get('actor', '').strip().lower()
        
        # Requête de base
        movies_query = Movie.query
        
        # Filtre par titre ou description
        if query:
            movies_query = movies_query.filter(
                db.or_(
                    Movie.title.ilike(f'%{query}%'),
                    Movie.description.ilike(f'%{query}%')
                )
            )
        
        # Filtre par genre
        if genre:
            movies_query = movies_query.join(Movie.genres).filter(
                db.func.lower(Genre.name).ilike(f'%{genre}%')
            )
        
        # Filtre par réalisateur
        if director:
            movies_query = movies_query.join(Movie.director).filter(
                db.func.lower(Director.name).ilike(f'%{director}%')
            )
        
        # Filtre par acteur
        if actor:
            movies_query = movies_query.join(Movie.actors).filter(
                db.func.lower(Actor.name).ilike(f'%{actor}%')
            )
        
        # Exécuter la requête et formater les résultats
        movies = movies_query.distinct().all()
        
        results = []
        for movie in movies:
            results.append({
                "id": movie.id,
                "title": movie.title,
                "poster_url": movie.poster_url,
                "video_path" : movie.video_file_path,
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
def get_all_movies():
    """Récupérer tous les films"""
    movies = Movie.query.all()
    return jsonify([{"id": m.id, "title": m.title, "poster_url":m.poster_url, "director_id": m.director_id, "video_path":m.video_file_path} for m in movies])

@movie_bp.route('/<int:id>', methods=['GET'])
def get_movie(id):
    """Récupérer un film spécifique"""
    movie = Movie.query.get(id)
    if not movie:
        return jsonify({"error": "Film non trouvé"}), 404
    return jsonify({"id": movie.id, "title": movie.title, "poster_url":movie.poster_url, "director_id": movie.director_id, "video_path":movie.video_file_path})

@movie_bp.route('/', methods=['POST'])
def create_movie():
    """Créer un film"""
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
def update_movie(id):
    """Mettre à jour un film"""
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
def delete_movie(id):
    """Supprimer un film"""
    movie = Movie.query.get(id)
    if not movie:
        return jsonify({"error": "Film non trouvé"}), 404

    db.session.delete(movie)
    db.session.commit()
    return jsonify({"message": "Film supprimé avec succès"})



@movie_bp.route('/full', methods=['POST'])
def create_full_movie():
    try:
        from app.models.actor import Actor
        from app.models.genre import Genre
        from app.models.director import Director
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

        # 📁 Upload de l'affiche
        poster_file = request.files.get('poster')
        poster_url = None
        if poster_file:
            folder = 'static/posters'
            os.makedirs(folder, exist_ok=True)
            filename = secure_filename(poster_file.filename)
            poster_path = os.path.join(folder, filename)
            poster_file.save(poster_path)
            poster_url = f'/static/posters/{filename}'

        # 📽️ Upload de la vidéo
        video_file = request.files.get('video')
        video_path = None
        if video_file:
            video_folder = 'static/videos'
            os.makedirs(video_folder, exist_ok=True)
            video_filename = secure_filename(video_file.filename)
            video_full_path = os.path.join(video_folder, video_filename)
            video_file.save(video_full_path)
            video_path = f'/static/videos/{video_filename}'

        # 🎬 Réalisateur
        director_key = director_name.replace(" ", "").upper()
        director = Director.query.filter(
            db.func.replace(db.func.upper(Director.name), " ", "") == director_key
        ).first()
        if not director:
            director = Director(name=director_name)
            db.session.add(director)

        # 🎥 Film
        movie = Movie(
            title=title,
            release_year=int(release_year) if release_year else None,
            rating=float(rating) if rating else None,
            description=description,
            poster_url=poster_url,
            video_file_path=video_path,  # 👈 Ajout du chemin de la vidéo
            director=director
        )

        # 👤 Acteurs
        for actor_name in actor_names:
            key = actor_name.replace(" ", "").upper()
            actor = Actor.query.filter(
                db.func.replace(db.func.upper(Actor.name), " ", "") == key
            ).first()
            if not actor:
                actor = Actor(name=actor_name)
                db.session.add(actor)
            movie.actors.append(actor)

        # 🎭 Genres
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


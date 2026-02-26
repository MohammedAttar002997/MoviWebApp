from data_manager import DataManager
from dotenv import load_dotenv
from flask import Flask, request, flash, redirect, url_for
from models import db, Movie
import os
import requests



app = Flask(__name__)
app.secret_key = 'development-key'


basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'data/movies.sqlite')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)  # Link the database and the app. This is the reason you need to import db from models


data_manager = DataManager()


load_dotenv()
MOVIES_API_KEY = os.getenv('API_KEY')
MOVIES_URL = f"https://www.omdbapi.com/?apikey={MOVIES_API_KEY}&t="

@app.route('/')
def home():
    return "Welcome to MoviWeb App!"


@app.route('/users')
def list_users():
    users = data_manager.get_user()
    return str(users)  # Temporarily returning users as a string


@app.route('/users', methods=['POST'])
def add_user():
    pass


@app.route('/users/<int:user_id>/movies', methods=['GET'])
def show_movies(user_id):
    pass


@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie(user_id):
    """
        Fetches movie details from OMDb API and adds them to a user's library.
        """
    # 1. Get the title from the form
    movie_title = request.form.get('title').strip()

    if not movie_title:
        flash("Please enter a movie title.", "warning")
        return redirect(url_for('get_user_movies', user_id=user_id))

    try:
        # 2. Call the OMDb API (using the variables you defined earlier)
        # We use a timeout to keep the app responsive
        response = requests.get(f"{MOVIES_URL}{movie_title}", timeout=5)
        response.raise_for_status()
        movie_data = response.json()

        # 3. Check if the movie was actually found by the API
        if movie_data.get("Response") == "False":
            flash(f"Error from API: {movie_data.get('Error')}", "danger")
            return redirect(url_for('get_user_movies', user_id=user_id))

        # 4. Use DataManager to save the enriched data
        # We pull the specific fields OMDb provides (Title, Year, Director, Poster)
        movie = Movie(
            name = movie_data.get('Title'),
            director = movie_data.get('Director'),
            year = movie_data.get('Year'),
            poster = movie_data.get('Poster'),
            user_id = user_id
        )
        data_manager.add_movie(movie)

        flash(f"Successfully added '{movie_data.get('Title')}'!", "success")

    except requests.exceptions.RequestException as e:
        flash(f"Network error: Could not connect to Movie API. {str(e)}", "danger")
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "danger")

    return redirect(url_for('get_user_movies', user_id=user_id))


@app.route('/users/<int:user_id>/movies/<int:movie_id>/update', methods=['POST'])
def update_movie(user_id,movie_id):
    pass


@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_movie(user_id,movie_id):
    pass


if __name__ == '__main__':
  with app.app_context():
    db.create_all()

  app.run()
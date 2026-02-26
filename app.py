from data_manager import DataManager
from dotenv import load_dotenv
from flask import Flask, request, flash, redirect, url_for, render_template
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
    users = data_manager.get_users()
    return render_template('index.html', users=users)


@app.route('/users')
def list_users():
    users = data_manager.get_users()
    return str(users)  # Temporarily returning users as a string


@app.route('/users', methods=['POST'])
def add_user():
    """
    Handles the creation of a new user via the home page form.
    """
    # 1. Get the name from the form input (name="name" in your HTML)
    username = request.form.get('name')

    # 2. Basic Validation
    if not username or username.strip() == "":
        flash("Username cannot be empty!", "danger")
        return redirect(url_for('home'))

    try:
        # 4. Use DataManager to create the user
        data_manager.create_user(username.strip())

        flash(f"User '{username}' created successfully!", "success")

    except Exception as e:
        # Handle database errors (like a duplicate username if you set it to UNIQUE)
        flash(f"An error occurred: {str(e)}", "danger")

    # 5. Redirect back to the index page to show the updated list
    return redirect(url_for('home'))


@app.route('/users/<int:user_id>/movies', methods=['GET'])
def show_movies(user_id):
    """
    Fetches a specific user and all their associated movies to display on their profile.
    """
    # 1. Use DataManager to find the user
    user = data_manager.get_user_by_id(user_id)

    if not user:
        flash("User not found!", "danger")
        return redirect(url_for('home'))

    # 2. Get the movies (using the dynamic relationship)
    # This executes the query and returns the list of movies
    movies = user.users.all()

    # 3. Render the specific user's movie page
    return render_template('movies.html', user=user, movies=movies)



@app.route('/users/<int:user_id>/movies', methods=['POST'])
def add_movie(user_id):
    """
        Fetches movie details from OMDb API and adds them to a user's library.
        """
    # 1. Get the title from the form
    movie_title = request.form.get('title').strip()

    if not movie_title:
        flash("Please enter a movie title.", "warning")
        return redirect(url_for('show_movies', user_id=user_id))

    try:
        # 2. Call the OMDb API (using the variables you defined earlier)
        # We use a timeout to keep the app responsive
        response = requests.get(f"{MOVIES_URL}{movie_title}", timeout=5)
        response.raise_for_status()
        movie_data = response.json()

        # 3. Check if the movie was actually found by the API
        if movie_data.get("Response") == "False":
            flash(f"Error from API: {movie_data.get('Error')}", "danger")
            return redirect(url_for('show_movies', user_id=user_id))

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

    return redirect(url_for('show_movies', user_id=user_id))


@app.route('/users/<int:user_id>/update_movie/<int:movie_id>', methods=['GET', 'POST'])
def update_movie(user_id, movie_id):
    """
    Handles updating ONLY the movie title for a specific movie.
    """
    # 1. Fetch the movie object from the DB
    movie = Movie.query.get(movie_id)

    if not movie:
        flash("Movie not found!", "danger")
        return redirect(url_for('show_movies', user_id=user_id))

    if request.method == 'POST':
        # 2. Get the new title from the form
        new_title = request.form.get('title')

        if new_title:
            # 3. Call your DataManager method
            # We pass the 'movie' object and the 'new_title' string as your method requires
            success = data_manager.update_movie(movie, new_title)

            if success:
                # Also updating 'movie.title' in case your DataManager only touched 'movie.name'
                movie.title = new_title
                db.session.commit()
                flash(f"Movie title updated to '{new_title}'!", "success")
            else:
                flash("Update failed.", "danger")
        else:
            flash("Title cannot be empty!", "warning")

        return redirect(url_for('show_movies', user_id=user_id))

    # 4. GET request: Show the simple edit form
    return render_template('update_movie.html', user_id=user_id, movie=movie)

@app.route('/users/<int:user_id>/movies/<int:movie_id>/delete', methods=['POST'])
def delete_movie(user_id, movie_id):
    """
    Deletes a specific movie from a user's collection.
    """
    try:
        # 1. Use DataManager to perform the deletion
        # If you implemented the 'Scoped Security' version, use that here:
        success = data_manager.delete_movie(movie_id)

        if success:
            flash("Movie was successfully removed from your collection.", "success")
        else:
            flash("Error: Movie not found or could not be deleted.", "danger")

    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "danger")

    # 2. Redirect back to the user's movie list page
    return redirect(url_for('show_movies', user_id=user_id))


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
  with app.app_context():
    db.create_all()

  app.run()
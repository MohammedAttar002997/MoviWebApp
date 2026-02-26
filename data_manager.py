from models import db, User, Movie

class DataManager:
    # Define Crud operations as methods


    def create_user(self, name):
        new_user = User(username = name)
        db.session.add(new_user)
        db.session.commit()
        return new_user


    def get_user_by_id(self, user_id):
        """Helper method to find a specific user."""
        return User.query.get(user_id)


    def get_user(self):
        return User.query.all()


    def get_movies(self, user_id):
        """
                Retrieves movies for a specific user.
                Since you used lazy='dynamic', we can query the relationship directly!
                """
        user = self.get_user_by_id(user_id)
        if user:
            # Because of lazy='dynamic', .users is a query we can execute
            return user.users.all()
        return []


    def add_movie(self, movie):
        """Creates and adds a movie linked to a specific user."""
        new_movie = movie
        db.session.add(new_movie)
        db.session.commit()
        return new_movie


    def delete_movie(self, movie_id):
        """Deletes a movie from the database."""
        movie = Movie.query.get(movie_id)
        if movie:
            db.session.delete(movie)
            db.session.commit()
            return True
        return False


    def update_movie(self, movie,new_title):
        """Updates a movie linked to a specific user."""
        movie = Movie.query.get(movie.id)
        if movie:
            if new_title:
                movie.name = new_title
            db.session.commit()
            return True
        return False

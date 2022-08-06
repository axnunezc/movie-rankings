from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
from decouple import config

API_KEY = config("API_KEY")
API_ENDPOINT = "https://api.themoviedb.org/3/search/movie"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 (e.g. 7.5)", validators=[DataRequired()])
    review = StringField("Your Review", validators=[DataRequired()])
    submit = SubmitField("Done")
    
class AddMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///new-books-collection.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), nullable=False)

    def __repr__(self):
        return f'<Movie {self.title}>'
    
db.create_all()

@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    return render_template("index.html", movies=all_movies)

@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = RateMovieForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        new_rating = form.rating.data
        new_review = form.review.data
        movie.rating = new_rating
        movie.review = new_review
        db.session.commit()  
        return redirect(url_for("home"))
    return render_template("edit.html", form=form, movie=movie)

@app.route("/delete")
def delete():
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/add", methods=["GET", "POST"])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_params = {
            "api_key": API_KEY,
            "query": form.title.data
        }
        response = requests.get(API_ENDPOINT, params=movie_params).json()["results"]
        return render_template("select.html", movies=response)
    return render_template("add.html", form=form)

@app.route("/details")
def details():
    movie_id = request.args.get("id")
    get_details_endpoint = f"https://api.themoviedb.org/3/movie/{movie_id}"
    get_details_params = {
        "api_key": API_KEY
    }
    response = requests.get(get_details_endpoint, params=get_details_params).json()
    new_movie = Movie(
    title=response["original_title"],
    year=response["release_date"][0:4],
    description=response["overview"],
    img_url=f"https://image.tmdb.org/t/p/w500{response['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for("edit", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)

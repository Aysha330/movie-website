from flask import Flask, jsonify, request, render_template, redirect, url_for, session
import requests
import mysql.connector
from auth import auth_bp

app = Flask(__name__)
app.register_blueprint(auth_bp)
app.secret_key = "supersecretkey"  # needed for session management

# ✅ Connect to MySQL database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="ainu@3386",  # change this to your actual password
    database="movienest_db"
)
cursor = db.cursor(dictionary=True)

TMDB_API_KEY = "dcd237164402f65274a94d11e130246c"

# Home page
@app.route("/")
def home():
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=en-US&page=1"
    response = requests.get(url).json()
    movies = []
    for m in response.get("results", []):
        movies.append({
            "title": m.get("title", "N/A"),
            "year": m.get("release_date","")[:4] if m.get("release_date") else "N/A",
            "poster": f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get("poster_path") else "https://via.placeholder.com/200x300?text=No+Image",
            "overview": m.get("overview","No overview available.")
        })
    if "user_id" in session:
        # render your main page here, e.g., index.html
        return render_template("index.html")  
    else:
        # Not logged in → show login page
        return render_template("login.html")

# Search movies
@app.route("/search")
def search():
    query = request.args.get("q")
    if not query:
        return jsonify([])

    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
    response = requests.get(url).json()

    results = []
    for movie in response.get("results", []):
        results.append({
            "title": movie.get("title", "N/A"),
            "year": movie.get("release_date", "")[:4] if movie.get("release_date") else "N/A",
            "poster": f"https://image.tmdb.org/t/p/w200{movie.get('poster_path')}" if movie.get("poster_path") else "https://via.placeholder.com/200x300?text=No+Image",
            "overview": movie.get("overview", "No description available.")
        })

    return jsonify(results)

# Add to watchlist
@app.route("/add_to_watchlist", methods=["POST"])
def add_to_watchlist():
    if "user_id" not in session:
        return redirect(url_for("auth.login_form"))

    movie = {
        "title": request.form.get("title"),
        "year": request.form.get("year"),
        "poster": request.form.get("poster"),
        "overview": request.form.get("overview")
    }

    user_id = session["user_id"]

    cursor.execute("SELECT * FROM watchlist WHERE user_id = %s AND title = %s", (user_id, movie["title"]))
    existing = cursor.fetchone()

    if existing:
        return jsonify({"message": f"{movie['title']} is already in your watchlist."})
    else:
        cursor.execute(
            "INSERT INTO watchlist (user_id, title, year, poster, overview) VALUES (%s, %s, %s, %s, %s)",
            (user_id, movie["title"], movie["year"], movie["poster"], movie["overview"])
        )
        db.commit()
        return jsonify({"message": f"{movie['title']} added to your watchlist!"})

# Watchlist page
@app.route("/watchlist")
def view_watchlist():
    if "user_id" not in session:
        return redirect(url_for("auth.login_form"))
    user_id = session["user_id"]
    cursor.execute("SELECT * FROM watchlist WHERE user_id = %s", (user_id,))
    movies = cursor.fetchall()
    return render_template("watchlist.html", movies=movies)

# Mark as watched
@app.route("/mark_as_watched", methods=["POST"])
def mark_as_watched():
    if "user_id" not in session:
        return redirect(url_for("auth.login_form"))
    user_id = session["user_id"]

    title = request.form.get("title")
    year = request.form.get("year")
    poster = request.form.get("poster")
    overview = request.form.get("overview")

    # Remove from watchlist
    cursor.execute("DELETE FROM watchlist WHERE user_id = %s AND title = %s", (user_id, title))

    # Add to watched if not already
    cursor.execute("SELECT * FROM watched WHERE user_id = %s AND title = %s", (user_id, title))
    existing = cursor.fetchone()
    if existing:
        db.commit()
        return jsonify({"message": f"{title} is already in your watched list."})
    else:
        cursor.execute(
            "INSERT INTO watched (user_id, title, year, poster, overview) VALUES (%s, %s, %s, %s, %s)",
            (user_id, title, year, poster, overview)
        )
        db.commit()
        return jsonify({"message": f"{title} marked as watched!"})

# Remove from watched
@app.route("/remove_from_watched", methods=["POST"])
def remove_from_watched():
    if "user_id" not in session:
        return redirect(url_for("auth.login_form"))
    user_id = session["user_id"]
    title = request.form.get("title")
    cursor.execute("DELETE FROM watched WHERE user_id = %s AND title = %s", (user_id, title))
    db.commit()
    return jsonify({"message": f"{title} removed from watched list!"})

# Watched page
@app.route("/watched")
def view_watched():
    if "user_id" not in session:
        return redirect(url_for("auth.login_form"))
    user_id = session["user_id"]
    cursor.execute("SELECT * FROM watched WHERE user_id = %s", (user_id,))
    movies = cursor.fetchall()
    return render_template("watched.html", movies=movies)

# Popular & Genre page
@app.route("/popular")
def popular_page():
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=en-US&page=1"
    response = requests.get(url).json()
    movies = []
    for m in response.get("results", []):
        movies.append({
            "title": m.get("title", "N/A"),
            "year": m.get("release_date","")[:4] if m.get("release_date") else "N/A",
            "poster": f"https://image.tmdb.org/t/p/w500{m.get('poster_path')}" if m.get("poster_path") else "",
            "overview": m.get("overview","No overview available.")
        })
    return render_template("popular.html", movies=movies)

# 🔍 FIXED Popular search endpoint
@app.route("/popular/search")
def popular_search():
    genres = request.args.get("genres")
    user_lang = request.args.get("language")  # new query param for language
    page = int(request.args.get("page",1))

    url = "https://api.themoviedb.org/3/discover/movie"

    # 🌍 Language mapping
    language_mapping = {
        "english": "en",
        "hindi": "hi",
        "malayalam": "ml",
        "tamil": "ta",
        "telugu": "te",
        "bengali": "bn",
        "kannada": "kn",
        "marathi": "mr",
        "punjabi": "pa",
        "gujarati": "gu",
        "odia": "or",
        "assamese": "as",
        "urdu": "ur",
        "french": "fr",
        "spanish": "es",
        "italian": "it",
        "turkish": "tr",
        "korean": "ko",
        "chinese": "zh",
        "japanese": "ja",
        "thai": "th",
        "arabic": "ar",
        "russian": "ru",
        "german": "de",
        "portuguese": "pt",
    }

    import datetime
    today = datetime.date.today()
    start_date = today.replace(year=today.year-10)  # last 10 years

    params = {
        "api_key": TMDB_API_KEY,
        "sort_by": "popularity.desc",
        "page": page,
        "include_adult": False,
        "language": "en-US",
        "primary_release_date.gte": start_date,
        "primary_release_date.lte": today
    }

    if genres:
        params["with_genres"] = genres

    results = []

    if user_lang:
        user_lang = user_lang.lower()
        lang_code = language_mapping.get(user_lang)
        if lang_code:
            params["with_original_language"] = lang_code
            response = requests.get(url, params=params).json()
            results = response.get("results", [])
        else:
            return jsonify([])  # unknown language
    elif not genres and not user_lang:
        # if no filter, return popular movies
        url_pop = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=en-US&page={page}"
        response = requests.get(url_pop).json()
        results = response.get("results", [])
    else:
        response = requests.get(url, params=params).json()
        results = response.get("results", [])

    # prepare final output
    final_results = []
    for movie in results:
        final_results.append({
            "title": movie.get("title","N/A"),
            "year": movie.get("release_date","")[:4] if movie.get("release_date") else "N/A",
            "poster": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" 
                      if movie.get("poster_path") else "https://via.placeholder.com/200x300?text=No+Image",
            "overview": movie.get("overview","No description available.")
        })

    return jsonify(final_results)


# Toggle watchlist
@app.route("/toggle_watchlist", methods=["POST"])
def toggle_watchlist():
    if "user_id" not in session:
        return jsonify({"error": "login required"}), 401
    user_id = session["user_id"]
    title = request.form.get("title")
    year = request.form.get("year")
    poster = request.form.get("poster")
    overview = request.form.get("overview")

    cursor.execute("SELECT * FROM watchlist WHERE user_id=%s AND title=%s", (user_id, title))
    exists = cursor.fetchone()

    if exists:
        cursor.execute("DELETE FROM watchlist WHERE user_id=%s AND title=%s", (user_id, title))
        db.commit()
        return jsonify({"status":"removed"})
    else:
        cursor.execute(
            "INSERT INTO watchlist (user_id, title, year, poster, overview) VALUES (%s,%s,%s,%s,%s)",
            (user_id, title, year, poster, overview)
        )
        db.commit()
        return jsonify({"status":"added"})


# Toggle watched
@app.route("/toggle_watched", methods=["POST"])
def toggle_watched():
    if "user_id" not in session:
        return jsonify({"error": "login required"}), 401
    user_id = session["user_id"]
    title = request.form.get("title")
    year = request.form.get("year")
    poster = request.form.get("poster")
    overview = request.form.get("overview")

    cursor.execute("SELECT * FROM watched WHERE user_id=%s AND title=%s", (user_id, title))
    exists = cursor.fetchone()

    if exists:
        cursor.execute("DELETE FROM watched WHERE user_id=%s AND title=%s", (user_id, title))
        db.commit()
        return jsonify({"status":"removed"})
    else:
        # Remove from watchlist if present
        cursor.execute("DELETE FROM watchlist WHERE user_id=%s AND title=%s", (user_id, title))
        cursor.execute(
            "INSERT INTO watched (user_id, title, year, poster, overview) VALUES (%s,%s,%s,%s,%s)",
            (user_id, title, year, poster, overview)
        )
        db.commit()
        return jsonify({"status":"added"})


# Check status
@app.route("/check_status")
def check_status():
    if "user_id" not in session:
        return jsonify({"in_watchlist": False, "in_watched": False})
    user_id = session["user_id"]
    title = request.args.get("title")
    cursor.execute("SELECT * FROM watchlist WHERE user_id=%s AND title=%s", (user_id, title))
    in_watchlist = bool(cursor.fetchone())
    cursor.execute("SELECT * FROM watched WHERE user_id=%s AND title=%s", (user_id, title))
    in_watched = bool(cursor.fetchone())
    return jsonify({"in_watchlist": in_watchlist, "in_watched": in_watched})

# Logout
@app.route("/logout")
def logout():
    session.clear()  # clears all session data
    return redirect(url_for("auth.login_form"))  # redirect to login

if __name__ == "__main__":
    app.run(debug=True)

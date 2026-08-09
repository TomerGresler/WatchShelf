import sqlite3
conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

def get_all_movies():
    c.execute("SELECT * FROM movies WHERE hidden = 0")
    return [_movie_dict(m) for m in c.fetchall()]

def get_movie_by_title_partialmatch(title):
    c.execute("SELECT * FROM movies WHERE title LIKE ? AND hidden = 0", (f"%{title}%",))
    return [_movie_dict(m) for m in c.fetchall()]

def get_movie_by_title(title):
    # exact title, intentionally NOT filtered by hidden - this is the unhide path
    c.execute("SELECT * FROM movies WHERE title = ?", (title,))
    return [_movie_dict(m) for m in c.fetchall()]

def get_movie_by_id(movie_id):
    c.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
    movie = c.fetchone()
    if movie is None:
        return None
    return _movie_dict(movie)

def _movie_dict(movie):
    return {
        "id": movie["id"], "title": movie["title"], "year": movie["year"],
        "genres": movie["genre"].split(","), "status": movie["status"],
        "rating": movie["rating"], "note": movie["note"], "hidden": bool(movie["hidden"])
    }

def add_movie(title, year, genres):
    genres_str = ",".join(genres)
    c.execute("SELECT * FROM movies WHERE title = ?", (title,))
    existing_matches = c.fetchall()

    for movie in existing_matches:
        if year == movie["year"] and genres_str == movie["genre"]:
            return None

    c.execute("INSERT INTO movies(title, year, genre) VALUES (?, ?, ?)", (title, year, genres_str))
    conn.commit()

    c.execute("SELECT * FROM movies WHERE title = ? AND year = ? AND genre = ?", (title, year, genres_str))
    new_movie = c.fetchone()
    return _movie_dict(new_movie)

def update_movie(movie_id, status=None, rating=None, note=None, hidden=None):
    c.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
    movie = c.fetchone()
    if movie is None:
        return None

    if status is None:
        status = movie["status"]
    if rating is None:
        rating = movie["rating"]
    if note is None:
        note = movie["note"]
    if hidden is None:
        hidden = movie["hidden"]

    if (rating is not None or note is not None) and status != "watched":
        status = "watched"

    c.execute(
        "UPDATE movies SET status = ?, rating = ?, note = ?, hidden = ? WHERE id = ?",
        (status, rating, note, hidden, movie_id)
    )
    conn.commit()
    return {"id": movie_id, "status": status, "rating": rating, "note": note, "hidden": bool(hidden)}
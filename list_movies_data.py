import sqlite3
import os
from movies_data import _movie_dict
conn = sqlite3.connect(os.environ.get('WATCHSHELF_DB', 'database.db'), check_same_thread=False)
conn.execute("PRAGMA foreign_keys = ON")
conn.row_factory = sqlite3.Row
c = conn.cursor()

def add_movie_to_list(list_id, movie_id):
    c.execute("SELECT * FROM lists WHERE id = ?", (list_id,))
    existing = c.fetchone()
    if existing is None:
        return None

    c.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
    existing = c.fetchone()
    if existing is None:
        return None

    c.execute("SELECT * FROM list_movies WHERE list_id = ? AND movie_id = ?", (list_id, movie_id))
    existing = c.fetchone()
    if existing is not None:
        return None

    c.execute("INSERT INTO list_movies VALUES (?, ?)", (list_id, movie_id))
    conn.commit()
    return {"list_id": list_id, "movie_id": movie_id}

def remove_movie_from_list(list_id, movie_id):
    c.execute("SELECT * FROM list_movies WHERE list_id = ? AND movie_id = ?", (list_id, movie_id))
    existing = c.fetchone()
    if existing is None:
        return None
    else:
        c.execute("DELETE FROM list_movies WHERE list_id = ? AND movie_id = ?", (list_id, movie_id))
        conn.commit()
    return {"list_id": list_id, "movie_id": movie_id}

def get_movies_in_list(list_id, sort=None):
    query = """
        SELECT movies.id, movies.title, movies.year, movies.genre,
               movies.status, movies.rating, movies.note, movies.hidden
        FROM movies
        JOIN list_movies ON movies.id = list_movies.movie_id
        WHERE list_movies.list_id = ? AND movies.hidden = 0
    """
    if sort == "title":
        query += " ORDER BY movies.title"
    elif sort == "year":
        query += " ORDER BY movies.year"
    elif sort == "rating":
        query += " ORDER BY movies.rating"

    c.execute(query, (list_id,))
    rows = c.fetchall()
    movies_list = []
    for movie in rows:
        movies_list.append(_movie_dict(movie))
    return movies_list

def list_exists(list_id):
    c.execute("SELECT * FROM lists WHERE id = ?", (list_id,))
    return c.fetchone() is not None
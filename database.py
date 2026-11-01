import sqlite3
import os
conn = sqlite3.connect(os.environ.get('WATCHSHELF_DB', 'database.db'), check_same_thread=False)
conn.execute("PRAGMA foreign_keys = ON")
c = conn.cursor()

c.execute("""
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        year INTEGER,
        genre TEXT
    )
""")

c.execute("""CREATE TABLE IF NOT EXISTS lists(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT
)""")

c.execute("""
                  CREATE TABLE IF NOT EXISTS list_movies (
            list_id INTEGER,
            movie_id INTEGER,
            PRIMARY KEY(list_id, movie_id),
            FOREIGN KEY (list_id) REFERENCES lists(id),
            FOREIGN KEY (movie_id) REFERENCES movies(id)
        )
""")

try:
    c.execute("ALTER TABLE movies ADD COLUMN status TEXT DEFAULT 'none'")
except sqlite3.OperationalError:
    pass # column already exists, nothing to do

try:
    c.execute("ALTER TABLE movies ADD COLUMN rating INTEGER")
except sqlite3.OperationalError:
    pass

try:
    c.execute("ALTER TABLE movies ADD COLUMN note TEXT")
except sqlite3.OperationalError:
    pass

try:
    c.execute("ALTER TABLE movies ADD COLUMN hidden INTEGER DEFAULT 0")
except sqlite3.OperationalError:
    pass

def seed_movie(title, year, genre, status="none", rating=None, note=None, hidden=0):
    c.execute("SELECT * FROM movies WHERE title = ? AND year = ? AND genre = ?", (title, year, genre))
    if c.fetchone() is not None:
        return
    c.execute(
        "INSERT INTO movies(title, year, genre, status, rating, note, hidden) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, year, genre, status, rating, note, hidden)
    )

# fix the wrong Toy Story year in databases that were seeded before
c.execute("UPDATE movies SET year = 1995 WHERE title = 'Toy Story' AND year = 1997 AND genre = 'family,animation,comedy'")

seed_movie("Inception", 2010, "Sci-fi")
seed_movie("Toy Story", 1995, "family,animation,comedy", status="watched", rating=5, note="still holds up")
seed_movie("Interstellar", 2014, "sci-fi,drama", status="want_to_watch")
seed_movie("Movie I Regret Watching", 2005, "drama", status="watched", rating=1, hidden=1)

conn.commit()


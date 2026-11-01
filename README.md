# WatchShelf

WatchShelf is a small REST API for keeping track of movies, built with FastAPI and SQLite.
You can add movies, mark them as watched or want to watch, give them a rating (1-5) and a note,
hide movies you don't want to see in the normal views, and group movies into lists.

The data is saved in a SQLite file called `database.db`. The tables are created and a few
example movies are added the first time the app starts.

## Endpoints

| Method | Path | What it does |
|--------|------|--------------|
| GET | `/` | Short message with the API name |
| GET | `/movies` | All movies that are not hidden. Add `?title=...` to search by part of the title |
| GET | `/movies/{title}` | Movies with this exact title, including hidden ones (this is how you find a hidden movie to unhide it) |
| GET | `/movies/id/{movie_id}` | One movie by id |
| POST | `/movies` | Add a movie. Returns 201, or 409 if the same title, year and genres already exist |
| PATCH | `/movies/{id}` | Change status, rating, note or hidden |
| GET | `/lists` | All lists. Add `?name=...` to search by part of the name |
| POST | `/lists` | Create a list. Returns 201, or 409 if the name is taken |
| GET | `/lists/{list_id}/movies` | Movies in a list (hidden ones are left out). Optional `?sort=title`, `year` or `rating` |
| POST | `/lists/{list_id}/movies` | Add a movie to a list. Returns 201, 404 if the list or movie doesn't exist, 409 if it's already in the list |
| DELETE | `/lists/{list_id}/movies/{movie_id}` | Remove a movie from a list |

A search with no matches returns 200 with an empty list.

### Updating a movie

All fields in the PATCH body are optional. A field you leave out (or send as `null`) is not changed.

- `status`: `"none"`, `"want_to_watch"` or `"watched"`
- `rating`: 1 to 5. Send `0` to clear the rating
- `note`: any text. Send `""` to clear the note
- `hidden`: `true` or `false`

If a request sets a rating or a note, the status is switched to `"watched"`.

The interactive docs are at http://127.0.0.1:8000/docs when the app is running.

## Run locally

Needs Python 3.13 (older 3.10+ should also work).

```bash
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The API is then at http://127.0.0.1:8000. The database file `database.db` is created in the
folder you run it from. To use a different file, set the `WATCHSHELF_DB` environment variable
to its path.

## Run with Docker

```bash
docker build -t watchshelf .
docker run -p 8000:8000 -v watchshelf-data:/data watchshelf
```

Inside the container the database is saved at `/data/database.db`. The `-v watchshelf-data:/data`
part puts that folder in a Docker volume called `watchshelf-data`, so your movies and lists are
still there after the container is stopped or removed.

## Example requests

Add a movie:

```bash
curl -X POST http://127.0.0.1:8000/movies \
  -H "Content-Type: application/json" \
  -d '{"title": "Up", "year": 2009, "genres": ["animation", "family"]}'
```

Search movies:

```bash
curl "http://127.0.0.1:8000/movies?title=toy"
```

Rate a movie (this also sets it to watched):

```bash
curl -X PATCH http://127.0.0.1:8000/movies/1 \
  -H "Content-Type: application/json" \
  -d '{"rating": 4, "note": "good ending"}'
```

Clear the rating and move it back to want to watch:

```bash
curl -X PATCH http://127.0.0.1:8000/movies/1 \
  -H "Content-Type: application/json" \
  -d '{"rating": 0, "status": "want_to_watch"}'
```

Create a list and add a movie to it:

```bash
curl -X POST http://127.0.0.1:8000/lists \
  -H "Content-Type: application/json" \
  -d '{"name": "Weekend"}'
```

```bash
curl -X POST http://127.0.0.1:8000/lists/1/movies \
  -H "Content-Type: application/json" \
  -d '{"movie_id": 1}'
```

Get the movies in a list sorted by year:

```bash
curl "http://127.0.0.1:8000/lists/1/movies?sort=year"
```

## Run the tests

```bash
pip install -r requirements.txt
pytest
```

The tests use FastAPI's TestClient and a temporary database, so your own `database.db` is not touched.
They also run on GitHub Actions on every push (`.github/workflows/tests.yml`).

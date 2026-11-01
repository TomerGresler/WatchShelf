import movies_data
import lists_data
import list_movies_data
import database


# root

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "/docs" in response.json()["message"]


# seed data

def test_toy_story_year_is_1995(client):
    movies = client.get("/movies/Toy Story").json()["movies"]
    assert len(movies) == 1
    assert movies[0]["year"] == 1995


# GET /movies

def test_get_all_movies_skips_hidden(client):
    titles = [m["title"] for m in client.get("/movies").json()["movies"]]
    assert "Inception" in titles
    assert "Movie I Regret Watching" not in titles


def test_search_movies_partial_match(client):
    response = client.get("/movies", params={"title": "incep"})
    assert response.status_code == 200
    assert [m["title"] for m in response.json()["movies"]] == ["Inception"]


def test_search_movies_no_results_is_empty_list(client):
    response = client.get("/movies", params={"title": "no such movie"})
    assert response.status_code == 200
    assert response.json() == {"movies": []}


def test_search_movies_skips_hidden(client):
    response = client.get("/movies", params={"title": "Regret"})
    assert response.json() == {"movies": []}


# GET /movies/{title}

def test_get_movie_by_exact_title_includes_hidden(client):
    response = client.get("/movies/Movie I Regret Watching")
    assert response.status_code == 200
    assert response.json()["movies"][0]["hidden"] is True


def test_get_movie_by_title_not_found(client):
    assert client.get("/movies/Not A Real Movie").status_code == 404


# GET /movies/id/{movie_id}

def test_get_movie_by_id(client, new_movie):
    movie = new_movie()
    response = client.get(f"/movies/id/{movie['id']}")
    assert response.status_code == 200
    assert response.json() == movie


def test_get_movie_by_id_not_found(client):
    assert client.get("/movies/id/999999").status_code == 404


# POST /movies

def test_add_movie_returns_201(client):
    response = client.post("/movies", json={"title": "Up", "year": 2009, "genres": ["animation", "family"]})
    assert response.status_code == 201
    movie = response.json()["movie"]
    assert movie["title"] == "Up"
    assert movie["genres"] == ["animation", "family"]
    assert movie["status"] == "none"
    assert movie["hidden"] is False


def test_add_movie_twice_returns_409(client):
    body = {"title": "Heat", "year": 1995, "genres": ["crime"]}
    assert client.post("/movies", json=body).status_code == 201
    response = client.post("/movies", json=body)
    assert response.status_code == 409


def test_add_movie_with_empty_genres(client, new_movie):
    movie = new_movie(genres=[])
    assert movie["genres"] == []
    assert client.get(f"/movies/id/{movie['id']}").json()["genres"] == []


def test_add_movie_genres_must_be_strings(client):
    response = client.post("/movies", json={"title": "Bad", "year": 2000, "genres": [1, 2]})
    assert response.status_code == 422


# PATCH /movies/{id}

def test_update_movie_not_found(client):
    assert client.patch("/movies/999999", json={"status": "watched"}).status_code == 404


def test_update_status(client, new_movie):
    movie = new_movie()
    response = client.patch(f"/movies/{movie['id']}", json={"status": "want_to_watch"})
    assert response.status_code == 200
    assert response.json()["movie"]["status"] == "want_to_watch"


def test_setting_rating_switches_to_watched(client, new_movie):
    movie = new_movie()
    patched = client.patch(f"/movies/{movie['id']}", json={"rating": 4}).json()["movie"]
    assert patched["rating"] == 4
    assert patched["status"] == "watched"


def test_setting_note_switches_to_watched(client, new_movie):
    movie = new_movie()
    patched = client.patch(f"/movies/{movie['id']}", json={"note": "nice"}).json()["movie"]
    assert patched["note"] == "nice"
    assert patched["status"] == "watched"


def test_rated_movie_can_go_back_to_want_to_watch(client, new_movie):
    # bug 1: a rated movie was forced back to watched on every update
    movie = new_movie()
    client.patch(f"/movies/{movie['id']}", json={"rating": 3})
    patched = client.patch(f"/movies/{movie['id']}", json={"status": "want_to_watch"}).json()["movie"]
    assert patched["status"] == "want_to_watch"
    assert patched["rating"] == 3
    assert client.get(f"/movies/id/{movie['id']}").json()["status"] == "want_to_watch"


def test_hiding_rated_movie_keeps_status(client, new_movie):
    movie = new_movie()
    client.patch(f"/movies/{movie['id']}", json={"rating": 3, "status": "watched"})
    client.patch(f"/movies/{movie['id']}", json={"status": "want_to_watch"})
    patched = client.patch(f"/movies/{movie['id']}", json={"hidden": True}).json()["movie"]
    assert patched["status"] == "want_to_watch"


def test_clear_rating_with_zero(client, new_movie):
    # bug 2: there was no way to clear a rating
    movie = new_movie()
    client.patch(f"/movies/{movie['id']}", json={"rating": 5, "note": "great"})
    patched = client.patch(f"/movies/{movie['id']}", json={"rating": 0}).json()["movie"]
    assert patched["rating"] is None
    assert patched["note"] == "great"
    assert client.get(f"/movies/id/{movie['id']}").json()["rating"] is None


def test_clear_note_with_empty_string(client, new_movie):
    movie = new_movie()
    client.patch(f"/movies/{movie['id']}", json={"rating": 2, "note": "meh"})
    patched = client.patch(f"/movies/{movie['id']}", json={"note": ""}).json()["movie"]
    assert patched["note"] is None
    assert patched["rating"] == 2


def test_clearing_does_not_switch_to_watched(client, new_movie):
    movie = new_movie()
    client.patch(f"/movies/{movie['id']}", json={"rating": 2})
    client.patch(f"/movies/{movie['id']}", json={"status": "want_to_watch"})
    patched = client.patch(f"/movies/{movie['id']}", json={"rating": 0, "note": ""}).json()["movie"]
    assert patched["status"] == "want_to_watch"


def test_rating_out_of_range(client, new_movie):
    movie = new_movie()
    assert client.patch(f"/movies/{movie['id']}", json={"rating": 6}).status_code == 422
    assert client.patch(f"/movies/{movie['id']}", json={"rating": -1}).status_code == 422


def test_invalid_status(client, new_movie):
    movie = new_movie()
    assert client.patch(f"/movies/{movie['id']}", json={"status": "maybe"}).status_code == 422


def test_hide_and_unhide_movie(client, new_movie):
    movie = new_movie()
    client.patch(f"/movies/{movie['id']}", json={"hidden": True})
    titles = [m["title"] for m in client.get("/movies").json()["movies"]]
    assert movie["title"] not in titles

    # exact title still finds it, so it can be unhidden
    found = client.get(f"/movies/{movie['title']}").json()["movies"][0]
    client.patch(f"/movies/{found['id']}", json={"hidden": False})
    titles = [m["title"] for m in client.get("/movies").json()["movies"]]
    assert movie["title"] in titles


# GET /lists and POST /lists

def test_create_list_returns_201(client):
    response = client.post("/lists", json={"name": "Weekend"})
    assert response.status_code == 201
    assert response.json()["list"]["name"] == "Weekend"


def test_create_list_twice_returns_409(client):
    assert client.post("/lists", json={"name": "Classics"}).status_code == 201
    assert client.post("/lists", json={"name": "Classics"}).status_code == 409


def test_get_all_lists(client, new_list):
    created = new_list()
    response = client.get("/lists")
    assert response.status_code == 200
    assert created in response.json()["lists"]


def test_search_lists_partial_match(client, new_list):
    created = new_list()
    response = client.get("/lists", params={"name": created["name"][-4:]})
    assert response.status_code == 200
    assert created in response.json()["lists"]


def test_search_lists_no_results_is_empty_list(client):
    response = client.get("/lists", params={"name": "no such list"})
    assert response.status_code == 200
    assert response.json() == {"lists": []}


# /lists/{list_id}/movies

def test_add_movie_to_list_returns_201(client, new_list, new_movie):
    lst = new_list()
    movie = new_movie()
    response = client.post(f"/lists/{lst['id']}/movies", json={"movie_id": movie["id"]})
    assert response.status_code == 201
    assert response.json() == {"list_id": lst["id"], "movie_id": movie["id"]}


def test_add_movie_to_list_twice_returns_409(client, new_list, new_movie):
    lst = new_list()
    movie = new_movie()
    client.post(f"/lists/{lst['id']}/movies", json={"movie_id": movie["id"]})
    response = client.post(f"/lists/{lst['id']}/movies", json={"movie_id": movie["id"]})
    assert response.status_code == 409


def test_add_movie_to_missing_list(client, new_movie):
    movie = new_movie()
    response = client.post("/lists/999999/movies", json={"movie_id": movie["id"]})
    assert response.status_code == 404


def test_add_missing_movie_to_list(client, new_list):
    lst = new_list()
    response = client.post(f"/lists/{lst['id']}/movies", json={"movie_id": 999999})
    assert response.status_code == 404


def test_get_movies_in_list(client, new_list, new_movie):
    lst = new_list()
    movie = new_movie()
    client.post(f"/lists/{lst['id']}/movies", json={"movie_id": movie["id"]})
    response = client.get(f"/lists/{lst['id']}/movies")
    assert response.status_code == 200
    assert response.json()["movies"] == [movie]


def test_get_movies_in_missing_list(client):
    assert client.get("/lists/999999/movies").status_code == 404


def test_get_movies_in_list_skips_hidden(client, new_list, new_movie):
    # bug 3: hidden movies showed up in lists
    lst = new_list()
    shown = new_movie()
    hidden = new_movie()
    client.post(f"/lists/{lst['id']}/movies", json={"movie_id": shown["id"]})
    client.post(f"/lists/{lst['id']}/movies", json={"movie_id": hidden["id"]})
    client.patch(f"/movies/{hidden['id']}", json={"hidden": True})

    ids = [m["id"] for m in client.get(f"/lists/{lst['id']}/movies").json()["movies"]]
    assert ids == [shown["id"]]


def test_get_movies_in_list_sorted(client, new_list):
    lst = new_list()
    a = client.post("/movies", json={"title": "Sort B", "year": 1990, "genres": []}).json()["movie"]
    b = client.post("/movies", json={"title": "Sort A", "year": 2020, "genres": []}).json()["movie"]
    client.patch(f"/movies/{a['id']}", json={"rating": 5})
    client.patch(f"/movies/{b['id']}", json={"rating": 1})
    for movie in (a, b):
        client.post(f"/lists/{lst['id']}/movies", json={"movie_id": movie["id"]})

    def titles(sort):
        response = client.get(f"/lists/{lst['id']}/movies", params={"sort": sort})
        return [m["title"] for m in response.json()["movies"]]

    assert titles("title") == ["Sort A", "Sort B"]
    assert titles("year") == ["Sort B", "Sort A"]
    assert titles("rating") == ["Sort A", "Sort B"]


def test_get_movies_in_list_bad_sort(client, new_list):
    lst = new_list()
    assert client.get(f"/lists/{lst['id']}/movies", params={"sort": "genre"}).status_code == 422


def test_remove_movie_from_list(client, new_list, new_movie):
    lst = new_list()
    movie = new_movie()
    client.post(f"/lists/{lst['id']}/movies", json={"movie_id": movie["id"]})
    response = client.delete(f"/lists/{lst['id']}/movies/{movie['id']}")
    assert response.status_code == 200
    assert response.json() == {"list_id": lst["id"], "movie_id": movie["id"]}
    assert client.get(f"/lists/{lst['id']}/movies").json()["movies"] == []


def test_remove_movie_not_in_list(client, new_list):
    lst = new_list()
    assert client.delete(f"/lists/{lst['id']}/movies/999999").status_code == 404


# foreign keys

def test_foreign_keys_are_on():
    for module in (database, movies_data, lists_data, list_movies_data):
        assert module.conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1

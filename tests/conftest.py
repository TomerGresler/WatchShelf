import os
import tempfile

import pytest

# use a temporary database for the tests, has to be set before main is imported
os.environ["WATCHSHELF_DB"] = os.path.join(tempfile.mkdtemp(), "test.db")

from fastapi.testclient import TestClient
import main


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def new_movie(client):
    # every call adds a fresh movie with a unique title, so tests don't affect each other
    def make(genres=["drama"]):
        title = f"Test Movie {os.urandom(4).hex()}"
        response = client.post("/movies", json={"title": title, "year": 2000, "genres": genres})
        return response.json()["movie"]
    return make


@pytest.fixture
def new_list(client):
    def make():
        response = client.post("/lists", json={"name": f"Test List {os.urandom(4).hex()}"})
        return response.json()["list"]
    return make

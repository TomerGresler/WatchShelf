from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import Literal
import movies_data
import lists_data
import list_movies_data
import database

class ListCreate(BaseModel):
    name:str

class MovieAdd(BaseModel):
    title:str
    year:int
    genres:list

class MovieIdBody(BaseModel):
    movie_id: int

class MovieUpdate(BaseModel):
    status: Literal["none", "want_to_watch", "watched"] | None = None
    rating: int | None = Field(default=None, ge=1, le=5)
    note: str | None = None
    hidden: bool | None = None
app = FastAPI()
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/movies")
async def movies(title: str | None = None):
    if title:
        movies_list = movies_data.get_movie_by_title_partialmatch(title)
        if not movies_list:
            raise HTTPException(status_code=404, detail="Movie not found")
    else:
        movies_list = movies_data.get_all_movies()
    return {"movies": movies_list }

@app.get("/movies/{title}")
async def get_movie(title: str):
    movies = movies_data.get_movie_by_title(title)
    if not movies:
        raise HTTPException(status_code=404, detail="Movie not found")
    return {"movies": movies}

@app.get("/movies/id/{movie_id}")
async def get_movie_by_id(movie_id: int):
    movie = movies_data.get_movie_by_id(movie_id)
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

@app.post("/movies")
async def post_movie(movie: MovieAdd):
    added = movies_data.add_movie(movie.title, movie.year, movie.genres)
    if added is None:
        raise HTTPException(status_code=404, detail="Movie already exists")
    return {"movie": added}

@app.patch("/movies/{id}")
async def patch_movie(id: int, movie: MovieUpdate):
    patched = movies_data.update_movie(id, movie.status, movie.rating, movie.note, movie.hidden)
    if patched is None:
        raise HTTPException(status_code=404, detail="Movie not found")
    return {"movie": patched}

@app.get("/lists")
async def lists(name: str | None = None):
    if name:
        lists_list = lists_data.get_list_by_name_partialmatch(name)
        if not lists_list:
            raise HTTPException(status_code=404, detail="List not found")
    else:
        lists_list = lists_data.get_all_lists()
    return {"lists": lists_list }

@app.post("/lists")
async def post_list(list_data: ListCreate):
    added = lists_data.create_list(list_data.name)
    if added is None:
        raise HTTPException(status_code=404, detail="List already exists")
    return {"list": added}

@app.get("/lists/{list_id}/movies")
async def get_list_movies(list_id: int, sort: Literal["title", "year", "rating"] | None = None):
    if not list_movies_data.list_exists(list_id):
        raise HTTPException(status_code=404, detail="List not found")
    return {"movies": list_movies_data.get_movies_in_list(list_id, sort)}

@app.post("/lists/{list_id}/movies")
async def add_list_movie(list_id: int, body: MovieIdBody):
    added = list_movies_data.add_movie_to_list(list_id, body.movie_id)
    if added is None:
        raise HTTPException(status_code=404, detail="Could not add movie. Movie not found, list not found, or already in list")
    return added

@app.delete("/lists/{list_id}/movies/{movie_id}")
async def delete_list_movie(list_id: int, movie_id: int):
    deleted = list_movies_data.remove_movie_from_list(list_id, movie_id)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Movie not in this list")
    return deleted

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)


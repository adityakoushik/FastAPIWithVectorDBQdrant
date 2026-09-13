# FastAPI with Qdrant

A small learning project for storing and searching three-dimensional document vectors with FastAPI and a local Qdrant server. The example vectors are written by hand so you can explore collections, points, and cosine similarity before adding an embedding model.

## Start on a new computer

Install [Git](https://git-scm.com/downloads), [uv](https://docs.astral.sh/uv/getting-started/installation/), and [Docker Desktop](https://docs.docker.com/get-started/get-docker/). Start Docker Desktop before running Qdrant. The project uses Python 3.14; uv will use the version in `.python-version` when it sets up the environment.

```sh
git clone https://github.com/adityakoushik/FastAPIWithVectorDBQdrant.git
cd FastAPIWithVectorDBQdrant
uv sync
```

Start Qdrant in one terminal:

```sh
docker run --name fastapi-qdrant -p 6333:6333 -v fastapi-qdrant-data:/qdrant/storage qdrant/qdrant
```

Then start the API in another terminal from the repository folder:

```sh
uv run uvicorn backend.main:app --reload
```

Open <http://127.0.0.1:8000/docs> to try the endpoints in Swagger UI. Run them in this order:

1. `GET /health` checks the Qdrant connection.
2. `POST /collections/documents` creates the `documents` collection with three-dimensional vectors and cosine similarity.
3. `POST /documents/seed` inserts three example documents.
4. `GET /documents/search` searches with the example vector `[0.9, 0.1, 0.0]`.

The Qdrant data lives in a Docker volume on your computer, so the collection and points are not included in Git. To start the same container again after stopping it, use `docker start fastapi-qdrant`. To stop it, use `docker stop fastapi-qdrant`.

After the first clone, get new commits from the repository folder with `git pull` and update dependencies with `uv sync`.

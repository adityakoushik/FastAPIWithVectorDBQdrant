# FastAPI With Vector DB Qdrant

This workspace has two app areas:

- `backend/`: FastAPI, Python package, tests, uv project files, and backend runtime config examples.
- `frontend/`: React/Vite document workspace.

Backend work should be done from the `backend` directory:

```sh
cd backend
uv sync
uv run fastapi dev
uv run python -m unittest discover -s tests -v
```

Frontend work should be done from the `frontend` directory:

```sh
cd frontend
npm ci
npm run dev
```

See `backend/README.md` and `frontend/README.md` for detailed setup and runtime notes.

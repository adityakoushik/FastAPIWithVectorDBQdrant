# IntelliDocs React frontend

A modular React (JavaScript / JSX) workspace for the currently mounted FastAPI API. PDF ingestion uses `POST /documents/upload`; semantic search uses `POST /search`, matching the currently mounted backend routes.

## Run locally

Requirements: Node.js 22.12+ (Node 24 recommended), npm, and the backend Python environment.

Terminal 1, from the `backend` directory:

```sh
uv sync
uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2, from `frontend`:

```sh
npm ci
npm run dev
```

Open http://localhost:5173. Vite proxies `/api/` to `http://127.0.0.1:8000/` for uploads and search. No backend CORS change is needed for this same-origin setup. Indexing and search require the configured Qdrant service and embedding model; the model may download weights on first use.

Optional: copy `.env.example` to `.env.local` and change `API_PROXY_TARGET` for a different development backend. `VITE_API_BASE_URL` is public build-time configuration; never put secrets in Vite variables. An absolute cross-origin URL requires explicit CORS configuration on the API.

## Features and boundaries

- Single PDF upload via file chooser or drag and drop; client validation for extension, empty files, and a 20 MB limit.
- Pending, error, retry, cancellation, and two-minute timeout handling; validates successful API responses.
- Optional upload category; session list with backend document IDs, page counts, and indexed chunk counts. Upload responses contain metadata, not full page text.
- Semantic search defaults to the selected document; choose All documents to include earlier sessions. Without a selected document, All documents is selected. Switching documents resets the search and cancels any pending request. Search supports optional category, result limit (1–20), and minimum score (−1 to 1). Leave limit and score blank to use the backend configuration; explicit zero and negative scores are supported. Category filtering uses an exact match. Results show passage text, similarity score, source, page, chunk index, category, and document ID when available.
- Responsive layout, keyboard controls, focus states, status announcements, and reduced-motion support.
- The upload list is held in React memory and resets on refresh. Indexed chunks remain in the backend and can be searched across sessions. Remove only removes a session entry; there is no server deletion endpoint.
- Scanned PDFs may have no text; the backend currently provides no OCR. Cancel aborts the client request; server indexing may still finish. A timed-out upload may have been indexed; search before retrying to avoid duplicate ingestion.
- This frontend does not add authentication, server document listing/deletion, or full-page retrieval. Those require additional backend APIs. Client validation is for usability, not server-side security: enforce file validation, request limits, access control, and rate limits at the backend/gateway before public exposure.

## Structure

```text
src/
  app/App.jsx                  Application shell and composition
  api/client.js                HTTP, API errors, response validation
  components/ErrorBoundary.jsx Unexpected UI failure recovery
  features/documents/           Upload, session list, semantic search, state hook
  lib/documents.js              File validation and size formatting
  styles/global.css            Responsive visual system
  test/                        API boundary and user-flow tests
```

## Checks

```sh
npm run lint
npm test
npm run build
npm run preview
```

The preview command is for local build inspection, not a production server.

## Production hosting

`npm run build` creates `dist/`. Serve it using a static web server and reverse-proxy `/api/` to FastAPI, stripping `/api`. The development proxy is not included in the production build.

A multi-stage `Dockerfile` and `nginx.conf` are included. Build with `docker build -t intellidocs-web .`. Run on a Docker network where the API resolves as `backend:8000`, or change `proxy_pass` to your API upstream. The backend must listen on `0.0.0.0` when accessed from another container. Example for an existing network with that backend alias:

```sh
docker run --rm --network intellidocs -p 8080:80 intellidocs-web
```

Terminate HTTPS at your deployment ingress. The supplied Nginx configuration sets security headers, limits request bodies, caches hashed assets, and prevents stale entry HTML. Dependency versions are locked in `package-lock.json`; use `npm ci` in CI and deployment. The Docker deployment requires your backend/network to be provisioned separately.

Passages below a provisional similarity score of 0.55 are labelled as related/weak matches; this presentation heuristic is not calibrated and does not change the backend retrieval threshold. Results are candidates, not verified answers.

# FastAPI with Qdrant

## Project Class 5 — Configuration + Dependency Lifecycle

এই lesson-এর explanation সরাসরি code-এর বাংলা comments ও docstrings-এ আছে।
এই ক্রমে পড়ো:

1. `src/backend/core/config.py`: `.env`, environment override, validation ও settings cache।
2. `src/backend/core/bootstrap.py`: সব dependencies বানিয়ে একে অন্যের সঙ্গে জোড়া দেওয়া।
3. `src/backend/core/container.py`: তৈরি controller ও client রাখার জায়গা।
4. `src/backend/main.py`: startup → request handling → shutdown; `yield` ও cleanup।
5. `src/backend/api/dependencies.py`: request-এ আগের controller ফেরত দেওয়া।
6. `src/backend/services/search_service.py`: user value না দিলে configured default নেওয়া।

`backend` folder থেকে `uv sync` চালাও। `.env.example` local `.env`-এর নমুনা;
`.env` Git-এ যাবে না। `INTC_` দিয়ে নতুন setting-এর নাম শুরু হয়।
`.env` বদলালে server restart করো। তারপর `uv run fastapi dev`।
বর্তমান API-তে `POST /documents/upload` ও `POST /search` আছে; নিচের demo
endpoint instructions আগের lesson-এর reference। Startup-এ embedding model load
হয়, তাই প্রথমবার model download লাগতে পারে। প্রতিটি worker নিজস্ব model রাখে।

Tests: `uv run python -m unittest discover -s tests -v`। Lifecycle tests fake
model/client দিয়ে চলে; live Qdrant বা model download লাগে না।

সূত্র: [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/) এবং
[Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)।

A small learning project for storing and searching three-dimensional document vectors with FastAPI and a local Qdrant server. The example vectors are written by hand so you can explore collections, points, and cosine similarity before adding an embedding model.

## Start on a new computer

Install [Git](https://git-scm.com/downloads), [uv](https://docs.astral.sh/uv/getting-started/installation/), and [Docker Desktop](https://docs.docker.com/get-started/get-docker/). Start Docker Desktop before running Qdrant. The project uses Python 3.14; uv will use the version in `.python-version` when it sets up the environment.

```sh
git clone https://github.com/adityakoushik/FastAPIWithVectorDBQdrant.git
cd FastAPIWithVectorDBQdrant/backend
uv sync
```

Start Qdrant in one terminal:

```sh
docker run --name fastapi-qdrant -p 6333:6333 -v fastapi-qdrant-data:/qdrant/storage qdrant/qdrant
```

Then start the API in another terminal from the backend folder:

```sh
uv run fastapi dev
```

Open <http://127.0.0.1:8000/docs> to try the endpoints in Swagger UI. Run them in this order:

1. `GET /health` checks the Qdrant connection.
2. `POST /collections/documents` creates the `documents` collection with three-dimensional vectors and cosine similarity.
3. `POST /documents/seed` inserts three example documents.
4. `GET /documents/search` searches with the example vector `[0.9, 0.1, 0.0]`.

The Qdrant data lives in a Docker volume on your computer, so the collection and points are not included in Git. To start the same container again after stopping it, use `docker start fastapi-qdrant`. To stop it, use `docker stop fastapi-qdrant`.

After the first clone, get new commits from the repository root with `git pull`, then update dependencies from `backend` with `uv sync`.

## React document workspace

The current `backend.main:app` mounts `POST /documents/upload` for PDF ingestion into Qdrant. The vector/health routes described above are historical and are not currently mounted.

PDF uploads use `SentenceAwareChunker` with an injected `SentenceSplitter`.
The default `SpacySentenceSplitter` uses a blank English pipeline with a
rule-based sentencizer; no trained model download is required. Whole sentences
are grouped within each page toward a 500-character budget, including joining
spaces. Page numbers are preserved and chunk indices run across the document.
Consecutive chunks carry up to one complete sentence of overlap within the same
page; older overlap sentences are dropped when needed to fit new text. Sentences
exceeding the budget use character windows with 50 characters of overlap. Every
chunk stays within 500 characters, and the final window is emitted only once.
Configure these with `chunk_size`, `overlap_sentences`, and `oversized_overlap`;
the latter must be nonnegative and smaller than `chunk_size` (set it explicitly
when using a budget of 50 or less). This is sentence-aware chunking, not
embedding-based semantic chunking.

Run the chunking, ingestion, repository, and PDF upload tests with `uv run python -m unittest discover -s tests -v`.

The React frontend lives in [frontend](../frontend/README.md). From this directory, run `uv run fastapi dev`. In a second terminal, run `cd ../frontend`, `npm ci`, and `npm run dev`, then open http://localhost:5173. See the frontend README for architecture, tests, environment variables, and production hosting.


## Batch embedding and vector ingestion

The upload pipeline is `PdfParser -> SentenceAwareChunker -> EmbeddingService.embed_batch -> VectorRepository`.
`QdrantVectorRepository` implements the storage contract; `DocumentService` has no Qdrant imports.
The composition root is `api/dependencies.py`. The sentence splitter and embedding service are cached,
so requests reuse the models. Blocking ingestion runs in a worker thread.

With Qdrant and the API running, upload a PDF using Swagger or:

```sh
curl -X POST http://localhost:8000/documents/upload -F "file=@handbook.pdf" -F "category=HR"
```

The response contains `filename`, `document_id`, `total_pages`, and `total_chunks`.
Each chunk has its own point UUID; payloads share the document UUID and include text,
page number, chunk index, source filename, and optional category. The repository rejects
mismatched chunk/vector counts and waits for Qdrant to apply the upsert before returning.
Empty/text-free PDFs return zero chunks without calling the model or database; OCR is not included.

`DOCUMENTS_COLLECTION` defaults to `documents_v2`; a missing collection is created with cosine
similarity and the actual embedding dimension. Existing collections must have a compatible vector
configuration. The default `all-MiniLM-L6-v2` model produces 384 dimensions and may download its
weights on first use. Each upload creates a new document ID, including repeated uploads.

Open http://localhost:6333/dashboard#/collections/documents_v2 to inspect points and metadata.
The integration check uploaded `integration-handbook.pdf` (two pages) and verified two 384-dimensional
points with category `integration-test` in the local dashboard. These sample points remain available.

Unit tests use a fake repository and mock embeddings; repository round-trip tests use in-memory
Qdrant, so the test suite needs neither a running Qdrant server nor downloaded model weights.
Legacy demo/search repository functions are retained in `vector_repository_old.py`; the active search endpoint uses the clean architecture described below. The existing React viewer expects a `pages` preview
response and needs adaptation to this ingestion-summary contract; use Swagger/curl for this stage.

## Clean search architecture

`POST /search` follows `SearchController -> SearchService -> EmbeddingService -> VectorRepository.search()`.
The Qdrant repository builds document_id and category filters (combined with AND) and maps scored points to application-owned
`SearchResult` models. The route and service do not depend on Qdrant types. Search reuses
the cached embedding model and the same configured collection as ingestion.

Upload a PDF first, then use Swagger at `/docs` or send:

```json
{
  "query": "How many casual leaves can employees take?",
  "limit": 3,
  "score_threshold": 0.4,
  "category": "HR"
}
```

Only `query` is required; the other fields default to `3`, `0.4`, and `null`.
The response includes `query`, `total_results`, and `results`. Each result contains
`id`, `score`, `text`, `document_id`, `source`, `category`, `page_number`, and
`chunk_index`. Missing optional metadata is returned as `null`; no matching points
returns an empty results list. The collection must already exist.

Search tests use fake embeddings/repositories and in-memory Qdrant, including category,
threshold, limit, metadata mapping, and HTTP response coverage.

`POST /search` accepts an optional nonempty `document_id` string. Supply the ID returned by upload to search only that PDF; omit it or pass null for all indexed documents. Filtering happens before vector ranking and result limiting. Unknown IDs return no matches. This is retrieval scoping, not an authorization boundary.


### PDF cleaning and source ranges

`PdfParser.extract_raw_pages(bytes)` retains the original sorted PyMuPDF text for inspection. `extract_pages(bytes)` removes repeated exact header/footer lines only in the top/bottom 8% of the page (at least two pages and half the document), removes matching Arabic page numbers in those margins, and normalizes whitespace. Unique margin notes and visible hyphens are retained. This is text-PDF cleanup, not OCR or a table reconstruction system.

Sentence chunking joins adjacent nonempty pages only when the previous page has no terminal punctuation and the next begins with a lowercase continuation rather than a list marker. This conservative heuristic may leave uppercase continuations separate. Cross-page chunks carry `page_number` and optional `page_end`; retrieval and the UI preserve the range. Old payloads without `page_end` remain supported.

Oversized sentences split at whitespace-delimited word boundaries. The character overlap is an upper bound, rounded to whole words and reduced when needed to fit new text. A single indivisible token longer than the budget is retained intact, so such a chunk can exceed the configured size. Ordinary sentence overlap is still conditional on available space.

Existing Qdrant payloads are not migrated automatically. Restart the backend and upload the PDF again to index cleaned text, then search the new current document. Re-upload creates a new document ID; older copies remain searchable under All documents.

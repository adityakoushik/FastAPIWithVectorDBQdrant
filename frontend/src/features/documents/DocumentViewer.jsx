import { useEffect, useRef, useState } from "react";
import { Search } from "lucide-react";
import { searchDocuments } from "../../api/client.js";

// Presentation heuristic only; calibrate on representative queries before tuning retrieval.
const CANDIDATE_SCORE = 0.55;

export function DocumentViewer({ document }) {
  const [scope, setScope] = useState(document ? "current" : "all");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [limit, setLimit] = useState("");
  const [threshold, setThreshold] = useState("");
  const [response, setResponse] = useState(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const request = useRef(null);
  useEffect(() => () => request.current?.abort(), []);

  async function search(event) {
    event.preventDefault();
    if (!query.trim() || request.current) return;
    const controller = new AbortController();
    request.current = controller;
    setPending(true);
    setError("");
    setResponse(null);
    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 120000);
    try {
      const result = await searchDocuments(
        {
          query,
          category,
          document_id: scope === "current" ? document.document_id : null,
          limit: limit === "" ? null : Number(limit),
          score_threshold: threshold === "" ? null : Number(threshold),
        },
        controller.signal,
      );
      if (!controller.signal.aborted) setResponse(result);
    } catch (failure) {
      if (timedOut)
        setError("Search timed out. Check the backend and try again.");
      else if (!controller.signal.aborted) setError(failure.message);
    } finally {
      clearTimeout(timeout);
      if (request.current === controller) {
        request.current = null;
        setPending(false);
      }
    }
  }

  return (
    <section className="viewer search-viewer" aria-labelledby="search-title">
      <div className="viewer-heading">
        <div>
          <span className="eyebrow">KNOWLEDGE BASE</span>
          <h2 id="search-title">Search your documents</h2>
        </div>
        <Search size={20} />
      </div>
      {document && (
        <div className="ingestion-summary" role="status">
          <strong>{document.filename}</strong>
          <span>
            {document.total_pages} pages · {document.total_chunks} indexed
            chunks{document.category ? ` · ${document.category}` : ""}
          </span>
          <small>Document ID: {document.document_id}</small>
          {document.total_chunks === 0 && (
            <p>
              No searchable text was found. Scanned PDFs may need OCR before
              upload.
            </p>
          )}
        </div>
      )}
      <form className="search-form" onSubmit={search}>
        <fieldset>
          <legend>Search in</legend>
          {["current", "all"].map((value) => (
            <label key={value}>
              <input
                type="radio"
                name="search-scope"
                value={value}
                checked={scope === value}
                disabled={pending || (value === "current" && !document)}
                onChange={() => {
                  setScope(value);
                  setResponse(null);
                  setError("");
                }}
              />
              {value === "current" ? "Current document" : "All documents"}
            </label>
          ))}
        </fieldset>
        <p>
          {scope === "current"
            ? `Search only ${document.filename}.`
            : "Search all indexed documents, including earlier sessions."}
        </p>
        <label className="field-label">
          Search query
          <input
            required
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="What would you like to find?"
          />
        </label>
        <div className="search-options">
          <label className="field-label">
            Category filter
            <input
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              placeholder="All categories"
              aria-describedby="search-options-help"
            />
          </label>
          <label className="field-label">
            Result limit
            <input
              type="number"
              min="1"
              max="20"
              step="1"
              placeholder="Server default"
              aria-describedby="search-options-help"
              value={limit}
              onChange={(event) => setLimit(event.target.value)}
            />
          </label>
          <label className="field-label">
            Minimum score
            <input
              type="number"
              min="-1"
              max="1"
              step="any"
              placeholder="Server default"
              aria-describedby="search-options-help"
              value={threshold}
              onChange={(event) => setThreshold(event.target.value)}
            />
          </label>
        </div>
        <p id="search-options-help">
          Leave limit and score blank to use server defaults. Limit: 1–20;
          score: −1 to 1. Category must match the uploaded category exactly.
        </p>
        <div className="search-actions">
          <button
            className="button primary"
            disabled={pending || !query.trim()}
            type="submit"
          >
            <Search size={16} />
            {pending ? "Searching…" : "Search"}
          </button>
          {pending && (
            <button
              className="button secondary"
              type="button"
              onClick={() => request.current?.abort()}
            >
              Cancel search
            </button>
          )}
        </div>
      </form>
      {error && (
        <div className="error-message" role="alert">
          {error}
        </div>
      )}
      <div className="search-results" aria-busy={pending}>
        <p role="status">
          {pending
            ? "Searching indexed chunks…"
            : response
              ? `${response.total_results} results for “${response.query}”`
              : "Enter a question or phrase to find relevant passages."}
        </p>
        {response?.total_results === 0 && (
          <p>
            No matching passages. Try another query, a lower minimum score, or
            clear the category filter.
          </p>
        )}
        {response?.total_results > 0 && (
          <div>
            <p>
              Passages are search candidates, not verified answers. Similarity
              scores are not probabilities.
            </p>
            {response.results.every(
              (result) => result.score < CANDIDATE_SCORE,
            ) && (
              <p>
                No strong matching passage found{" "}
                {scope === "current" ? "in this document" : "in this search"}.
                Showing related passages below.
              </p>
            )}
            <small>
              Scores below {CANDIDATE_SCORE} are marked as related passages
              using a provisional, uncalibrated cutoff.
            </small>
          </div>
        )}
        {response?.results.map((result) => (
          <article className="search-result" key={result.id}>
            <h3>{result.source || "Unknown source"}</h3>
            <p>
              {result.score < CANDIDATE_SCORE
                ? "Related passage · weak match"
                : "Matching passage · verify relevance"}
            </p>
            <div className="result-meta">
              <span>Score: {result.score.toFixed(3)}</span>
              {result.page_number != null && (
                <span>
                  Page {result.page_number}
                  {result.page_end > result.page_number
                    ? `–${result.page_end}`
                    : ""}
                </span>
              )}
              {result.chunk_index != null && (
                <span>Chunk {result.chunk_index}</span>
              )}
              {result.category != null && (
                <span>Category: {result.category}</span>
              )}
            </div>
            <p className="extracted-text">{result.text}</p>
            {result.document_id && (
              <small>Document ID: {result.document_id}</small>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

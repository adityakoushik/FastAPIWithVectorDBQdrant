import { useRef, useState } from "react";
import { ArrowUpRight, FileUp, LoaderCircle, Upload, X } from "lucide-react";

export function UploadPanel({ upload, pending, cancel, error, dismissError }) {
  const input = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [category, setCategory] = useState("");
  function accept(files) {
    setDragging(false);
    if (files?.length && !pending) upload(files[0], category);
  }
  return (
    <section className="upload-section" aria-labelledby="upload-heading">
      <div className="section-heading">
        <div>
          <span className="eyebrow">START WITH A DOCUMENT</span>
          <h2 id="upload-heading">
            A little less searching.
            <br />A lot more understanding.
          </h2>
          <p>
            Index your PDF for semantic search.
            <br className="desktop-break" /> Every page, in one focused
            knowledge base.
          </p>
        </div>
        <span className="decorative-arrow" aria-hidden="true">
          <ArrowUpRight size={32} />
        </span>
      </div>
      <label className="field-label upload-category">
        Category (optional)
        <input
          value={category}
          disabled={Boolean(pending)}
          onChange={(event) => setCategory(event.target.value)}
          placeholder="e.g. HR, Engineering"
        />
      </label>
      <div
        className={`dropzone ${dragging ? "dragging" : ""} ${pending ? "processing" : ""}`}
        onDragOver={(event) => {
          event.preventDefault();
          if (!pending) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          accept(event.dataTransfer.files);
        }}
      >
        <div className="upload-symbol">
          {pending ? (
            <LoaderCircle className="spin" size={27} />
          ) : (
            <FileUp size={27} />
          )}
        </div>
        <h3>{pending ? "Indexing your document…" : "Drop a PDF here"}</h3>
        <p className="upload-caption">
          {pending || "or choose a file from your computer"}
        </p>
        <input
          ref={input}
          type="file"
          accept=".pdf,application/pdf"
          aria-label="Choose PDF file"
          className="visually-hidden"
          disabled={Boolean(pending)}
          onChange={(event) => {
            accept(event.target.files);
            event.target.value = "";
          }}
        />
        {pending ? (
          <button className="button secondary" onClick={cancel}>
            <X size={16} />
            Cancel upload
          </button>
        ) : (
          <button
            className="button primary"
            onClick={() => input.current.click()}
          >
            <Upload size={16} />
            Choose PDF
          </button>
        )}
        <span className="file-hint">
          PDF files only · Up to 20 MB · One file at a time
        </span>
      </div>
      <div className="sr-status" role="status">
        {pending ? `Processing ${pending}` : ""}
      </div>
      {error && (
        <div className="error-message" role="alert">
          <span>{error}</span>
          <button
            className="icon-button"
            aria-label="Dismiss error"
            onClick={dismissError}
          >
            <X size={16} />
          </button>
        </div>
      )}
      <p className="session-note">
        <span className="small-dot" />
        This list resets on refresh. Indexed content stays in the backend.
        Canceling stops waiting; indexing may still finish.
      </p>
    </section>
  );
}

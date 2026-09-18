import { FileText, ArrowUpRight, Trash2 } from "lucide-react";
import { formatBytes } from "../../lib/documents.js";

export function DocumentList({ documents, selectedId, select, remove }) {
  return (
    <section className="document-list" aria-labelledby="documents-heading">
      <div className="list-heading">
        <h2 id="documents-heading">
          Your documents <span className="count">{documents.length}</span>
        </h2>
        <span className="muted">This session</span>
      </div>
      {!documents.length ? (
        <div className="empty-library">
          <div className="file-tile">
            <FileText size={22} />
          </div>
          <div>
            <h3>A fresh start</h3>
            <p>Your uploaded documents will appear here.</p>
          </div>
        </div>
      ) : (
        <ul className="document-items">
          {documents.map((document) => (
            <li
              key={document.id}
              className={document.id === selectedId ? "selected" : ""}
            >
              <button
                className="document-select"
                onClick={() => select(document.id)}
                aria-pressed={document.id === selectedId}
              >
                <span className="file-tile">
                  <FileText size={21} />
                </span>
                <span className="document-meta">
                  <strong>{document.filename}</strong>
                  <span>
                    {document.total_pages} pages · {document.total_chunks}{" "}
                    chunks · {formatBytes(document.size)}
                  </span>
                </span>
                <ArrowUpRight size={18} />
              </button>
              <button
                className="icon-button remove-button"
                onClick={() => remove(document.id)}
                aria-label={`Remove ${document.filename} from session`}
                title="Remove from this session only; indexed content stays in the backend"
              >
                <Trash2 size={16} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

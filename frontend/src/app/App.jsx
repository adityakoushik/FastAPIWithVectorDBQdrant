import {
  BookOpen,
  Files,
  Layers3,
  ArrowUpRight,
  FileText,
  TextSelect,
  PanelLeftClose,
} from "lucide-react";
import { useDocuments } from "../features/documents/useDocuments.js";
import { UploadPanel } from "../features/documents/UploadPanel.jsx";
import { DocumentList } from "../features/documents/DocumentList.jsx";
import { DocumentViewer } from "../features/documents/DocumentViewer.jsx";

export default function App() {
  const workspace = useDocuments();
  const pageCount = workspace.documents.reduce(
    (sum, document) => sum + document.total_pages,
    0,
  );
  const chunks = workspace.documents.reduce(
    (sum, document) => sum + document.total_chunks,
    0,
  );
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip to workspace
      </a>
      <aside className="sidebar">
        <a href="./" className="brand">
          <span className="brand-icon">
            <Layers3 size={23} />
          </span>
          intellidocs<span className="brand-period">.</span>
        </a>
        <span className="nav-label">WORKSPACE</span>
        <nav aria-label="Main navigation">
          <a className="nav-item active" href="#main">
            <Files size={18} />
            Documents
            <span className="nav-count">{workspace.documents.length}</span>
          </a>
        </nav>
        <div className="sidebar-note">
          <span className="note-icon">
            <BookOpen size={20} />
          </span>
          <h3>
            Your documents.
            <br />A clearer perspective.
          </h3>
          <p>A simple space to turn information into understanding.</p>
          <span className="note-line" />
        </div>
        <div className="sidebar-bottom">
          <span className="avatar">ID</span>
          <div>
            <strong>Personal workspace</strong>
            <span>Local session</span>
          </div>
          <PanelLeftClose size={16} aria-hidden="true" />
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <span>
            Workspace <span className="breadcrumb-slash">/</span>{" "}
            <strong>Documents</strong>
          </span>
          <span className="workspace-badge">
            <span className="small-dot" />
            PDF workspace
          </span>
        </header>
        <main id="main">
          <div className="page-heading">
            <div>
              <div className="eyebrow">LESS NOISE. MORE KNOWLEDGE.</div>
              <h1>
                Document workspace<span>.</span>
              </h1>
              <p>Bring your documents in. Get the important things out.</p>
            </div>
            <span className="heading-mark" aria-hidden="true">
              <ArrowUpRight size={26} />
            </span>
          </div>
          <div className="stats">
            <Stat
              icon={Files}
              label="Documents"
              value={workspace.documents.length.toString().padStart(2, "0")}
              detail="in this session"
            />
            <Stat
              icon={FileText}
              label="Pages extracted"
              value={pageCount.toString().padStart(2, "0")}
              detail="ready to explore"
            />
            <Stat
              icon={TextSelect}
              label="Indexed chunks"
              value={chunks.toLocaleString()}
              detail="from session uploads"
            />
          </div>
          <div className="workspace-grid">
            <div className="workspace-left">
              <UploadPanel {...workspace} />
              <DocumentList {...workspace} />
            </div>
            <DocumentViewer
              key={workspace.selected?.document_id || "all"}
              document={workspace.selected}
            />
          </div>
          <footer className="main-footer">
            <span>Made for a little more clarity.</span>
            <span>
              IntelliDocs <span className="footer-dot">·</span> Document
              intelligence
            </span>
          </footer>
        </main>
      </div>
    </div>
  );
}

function Stat({ icon: Icon, label, value, detail }) {
  return (
    <div className="stat">
      <div className="stat-top">
        <span>{label}</span>
        <Icon size={17} />
      </div>
      <div className="stat-bottom">
        <strong>{value}</strong>
        <span>{detail}</span>
      </div>
    </div>
  );
}

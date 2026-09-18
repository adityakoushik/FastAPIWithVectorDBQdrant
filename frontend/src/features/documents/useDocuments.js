import { useEffect, useRef, useState } from "react";
import { uploadDocument } from "../../api/client.js";
import { validatePdf } from "../../lib/documents.js";

export function useDocuments() {
  const [documents, setDocuments] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [pending, setPending] = useState(null);
  const [error, setError] = useState("");
  const request = useRef(null);
  useEffect(() => () => request.current?.abort(), []);

  async function upload(file, category = "") {
    if (request.current) return;
    const validation = validatePdf(file);
    if (validation) {
      setError(validation);
      return;
    }
    const controller = new AbortController();
    request.current = controller;
    setPending(file.name);
    setError("");
    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      controller.abort();
    }, 120000);
    try {
      const result = await uploadDocument(file, controller.signal, category);
      if (controller.signal.aborted) return;
      const document = {
        ...result,
        id: result.document_id,
        category: category.trim() || null,
        size: file.size,
        createdAt: new Date().toISOString(),
      };
      setDocuments((current) => [document, ...current]);
      setSelectedId(document.id);
    } catch (failure) {
      if (timedOut)
        setError(
          "Processing timed out after two minutes. The backend may still finish indexing this PDF. Check search before uploading again.",
        );
      else if (!controller.signal.aborted) setError(failure.message);
    } finally {
      clearTimeout(timeout);
      if (request.current === controller) {
        request.current = null;
        setPending(null);
      }
    }
  }

  function remove(id) {
    setDocuments((current) => current.filter((document) => document.id !== id));
    if (selectedId === id) setSelectedId(null);
  }

  return {
    documents,
    selectedId,
    select: setSelectedId,
    selected: documents.find((document) => document.id === selectedId),
    pending,
    error,
    upload,
    remove,
    cancel: () => request.current?.abort(),
    dismissError: () => setError(""),
  };
}

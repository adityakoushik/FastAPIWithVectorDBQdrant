import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import App from "../app/App.jsx";
import { uploadDocument, searchDocuments } from "../api/client.js";
import { validatePdf, MAX_FILE_BYTES } from "../lib/documents.js";

const response = {
  filename: "report.pdf",
  document_id: "doc-123",
  total_pages: 2,
  total_chunks: 4,
};
const searchResponse = {
  query: "green energy",
  total_results: 1,
  results: [
    {
      id: "chunk-1",
      score: 0.83,
      text: "Solar power is renewable.",
      source: "report.pdf",
      document_id: "doc-123",
      category: "Energy",
      page_number: 2,
      chunk_index: 0,
    },
  ],
};
const ok = (data) => ({ ok: true, json: async () => data });
const pdf = () =>
  new File(["%PDF-1.7 test"], "report.pdf", { type: "application/pdf" });

describe("document workspace", () => {
  it("explains a stale extraction-only backend instead of accepting it as indexed", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        ok({
          filename: "report.pdf",
          total_pages: 1,
          pages: [{ page_number: 1, text: "Legacy extraction" }],
        }),
      ),
    );
    await expect(uploadDocument(pdf())).rejects.toThrow("Restart the backend");
  });
  it("uses server defaults, preserves zero and negative scores, and resets overrides", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(
        ok({ query: "energy", total_results: 0, results: [] }),
      );
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.type(screen.getByLabelText("Search query"), "energy");
    const submit = () =>
      user.click(screen.getByRole("button", { name: "Search", exact: true }));
    const lastBody = () => JSON.parse(fetchMock.mock.lastCall[1].body);
    await submit();
    expect(lastBody()).toMatchObject({ limit: null, score_threshold: null });
    await user.type(screen.getByLabelText("Result limit"), "20");
    await user.type(screen.getByLabelText("Minimum score"), "0");
    await submit();
    expect(lastBody()).toMatchObject({ limit: 20, score_threshold: 0 });
    await user.clear(screen.getByLabelText("Minimum score"));
    await user.type(screen.getByLabelText("Minimum score"), "-0.125");
    await submit();
    expect(lastBody().score_threshold).toBe(-0.125);
    await user.clear(screen.getByLabelText("Result limit"));
    await user.clear(screen.getByLabelText("Minimum score"));
    await submit();
    expect(lastBody()).toMatchObject({ limit: null, score_threshold: null });
  });
  it("blocks search options outside backend bounds", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.type(screen.getByLabelText("Search query"), "energy");
    const limit = screen.getByLabelText("Result limit");
    const score = screen.getByLabelText("Minimum score");
    const submit = screen.getByRole("button", { name: "Search", exact: true });
    for (const value of ["0", "21", "1.5"]) {
      await user.clear(limit);
      await user.type(limit, value);
      expect(limit).toBeInvalid();
      await user.click(submit);
    }
    await user.clear(limit);
    for (const value of ["-1.1", "1.1"]) {
      await user.clear(score);
      await user.type(score, value);
      expect(score).toBeInvalid();
      await user.click(submit);
    }
    expect(fetchMock).not.toHaveBeenCalled();
  });
  it("uploads with category, displays ingestion metadata, and removes only the session entry", async () => {
    const fetchMock = vi.fn().mockResolvedValue(ok(response));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.type(screen.getByLabelText("Category (optional)"), "Energy");
    await user.upload(screen.getByLabelText("Choose PDF file"), pdf());
    expect(await screen.findByText("Document ID: doc-123")).toBeInTheDocument();
    expect(
      screen.getByText("2 pages · 4 indexed chunks · Energy"),
    ).toBeInTheDocument();
    expect(fetchMock.mock.calls[0][0]).toBe("/api/documents/upload");
    expect(fetchMock.mock.calls[0][1].body.get("file").name).toBe("report.pdf");
    expect(fetchMock.mock.calls[0][1].body.get("category")).toBe("Energy");
    await user.click(
      screen.getByRole("button", { name: "Remove report.pdf from session" }),
    );
    expect(screen.getByText("A fresh start")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
  it("renders a cross-page source range", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        ok({
          ...searchResponse,
          results: searchResponse.results.map((result) => ({
            ...result,
            page_end: 3,
          })),
        }),
      ),
    );
    const user = userEvent.setup();
    render(<App />);
    await user.type(screen.getByLabelText("Search query"), "green energy");
    await user.click(
      screen.getByRole("button", { name: "Search", exact: true }),
    );
    expect(await screen.findByText("Page 2–3")).toBeInTheDocument();
  });
  it("searches earlier uploads with filters and renders result metadata", async () => {
    const fetchMock = vi.fn().mockResolvedValue(ok(searchResponse));
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.type(screen.getByLabelText("Search query"), "green energy");
    await user.type(screen.getByLabelText("Category filter"), "Energy");
    await user.clear(screen.getByLabelText("Result limit"));
    await user.type(screen.getByLabelText("Result limit"), "5");
    await user.click(
      screen.getByRole("button", { name: "Search", exact: true }),
    );
    expect(
      await screen.findByText("Solar power is renewable."),
    ).toBeInTheDocument();
    expect(screen.getByText("Page 2")).toBeInTheDocument();
    expect(screen.getByText("Chunk 0")).toBeInTheDocument();
    expect(screen.getByText("Score: 0.830")).toBeInTheDocument();
    expect(fetchMock.mock.calls[0][0]).toBe("/api/search");
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      query: "green energy",
      limit: 5,
      score_threshold: null,
      category: "Energy",
      document_id: null,
    });
  });
  it("handles search errors, retry, and no results", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce({
          ok: false,
          status: 422,
          json: async () => ({ detail: [{ msg: "Invalid query" }] }),
        })
        .mockResolvedValueOnce(
          ok({ query: "nothing", total_results: 0, results: [] }),
        ),
    );
    const user = userEvent.setup();
    render(<App />);
    expect(
      screen.getByRole("button", { name: "Search", exact: true }),
    ).toBeDisabled();
    await user.type(screen.getByLabelText("Search query"), "nothing");
    await user.click(
      screen.getByRole("button", { name: "Search", exact: true }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid query");
    await user.click(
      screen.getByRole("button", { name: "Search", exact: true }),
    );
    expect(await screen.findByText(/No matching passages/)).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
  it("shows an upload error and allows retry with a text-free PDF", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          json: async () => ({}),
        })
        .mockResolvedValueOnce(ok({ ...response, total_chunks: 0 })),
    );
    const user = userEvent.setup();
    render(<App />);
    await user.upload(screen.getByLabelText("Choose PDF file"), pdf());
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "server could not process",
    );
    await user.upload(screen.getByLabelText("Choose PDF file"), pdf());
    expect(
      await screen.findByText(/No searchable text was found/),
    ).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
  it("cancels pending uploads without adding a document", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (_url, { signal }) =>
          new Promise((_resolve, reject) =>
            signal.addEventListener("abort", () =>
              reject(new DOMException("Aborted", "AbortError")),
            ),
          ),
      ),
    );
    const user = userEvent.setup();
    render(<App />);
    await user.upload(screen.getByLabelText("Choose PDF file"), pdf());
    await user.click(screen.getByRole("button", { name: "Cancel upload" }));
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Choose PDF" })).toBeEnabled(),
    );
    expect(screen.getByText("A fresh start")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
  it("rejects invalid, empty and oversized uploads", () => {
    expect(validatePdf({ name: "script.html", size: 10 })).toMatch("Only PDF");
    expect(validatePdf({ name: "empty.pdf", size: 0 })).toMatch("empty");
    expect(validatePdf({ name: "big.pdf", size: MAX_FILE_BYTES + 1 })).toMatch(
      "20 MB",
    );
    expect(validatePdf(pdf())).toBeNull();
  });
  it("rejects incompatible API responses including null payloads", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(ok(null)));
    await expect(uploadDocument(pdf())).rejects.toThrow(
      "unexpected document format",
    );
    await expect(searchDocuments({ query: "test" })).rejects.toThrow(
      "unexpected search format",
    );
  });
  it("omits blank upload categories and defers search defaults to the backend", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(ok(response))
      .mockResolvedValueOnce(
        ok({ query: "test", total_results: 0, results: [] }),
      );
    vi.stubGlobal("fetch", fetchMock);
    await uploadDocument(pdf(), undefined, "  ");
    expect(fetchMock.mock.calls[0][1].body.has("category")).toBe(false);
    await searchDocuments({ query: " test " });
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toEqual({
      query: "test",
      limit: null,
      score_threshold: null,
      category: null,
      document_id: null,
    });
  });
  it("explains network failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );
    await expect(uploadDocument(pdf())).rejects.toThrow(
      "Unable to reach the API",
    );
  });
});

it("defaults to the uploaded document, labels weak passages, and permits all documents", async () => {
  const fetchMock = vi
    .fn()
    .mockResolvedValueOnce(ok(response))
    .mockResolvedValue(
      ok({
        ...searchResponse,
        results: [{ ...searchResponse.results[0], score: 0.402 }],
      }),
    );
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();
  render(<App />);
  await user.upload(screen.getByLabelText("Choose PDF file"), pdf());
  await screen.findByText("Document ID: doc-123");
  expect(screen.getByLabelText("Current document")).toBeChecked();
  await user.type(screen.getByLabelText("Search query"), "holidays");
  await user.click(screen.getByRole("button", { name: "Search", exact: true }));
  expect(
    await screen.findByText(/No strong matching passage found/),
  ).toBeInTheDocument();
  expect(JSON.parse(fetchMock.mock.lastCall[1].body).document_id).toBe(
    "doc-123",
  );
  await user.click(screen.getByLabelText("All documents"));
  expect(
    screen.queryByText("Solar power is renewable."),
  ).not.toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "Search", exact: true }));
  await screen.findByText("Solar power is renewable.");
  expect(JSON.parse(fetchMock.mock.lastCall[1].body).document_id).toBeNull();
});

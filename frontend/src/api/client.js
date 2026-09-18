const baseUrl = (import.meta.env.VITE_API_BASE_URL || "/api").replace(
  /\/$/,
  "",
);

async function request(path, options) {
  let response;
  try {
    response = await fetch(`${baseUrl}${path}`, options);
  } catch (error) {
    if (options.signal?.aborted) throw error;
    throw new Error(
      "Unable to reach the API. Check that the backend is running, then try again.",
    );
  }
  if (!response.ok) {
    let detail;
    try {
      detail = (await response.json()).detail;
    } catch {
      /* Non-JSON proxy error. */
    }
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail
              .map((item) => item.msg)
              .filter(Boolean)
              .join("; ")
          : null;
    throw new Error(
      message ||
        `The server could not process this request (${response.status}). Check the backend and try again.`,
    );
  }
  try {
    return await response.json();
  } catch {
    throw new Error(
      "The API returned an unreadable response. Check the API URL configuration.",
    );
  }
}

const count = (value) => Number.isInteger(value) && value >= 0;
export async function uploadDocument(file, signal, category = "") {
  const body = new FormData();
  body.append("file", file);
  if (category.trim()) body.append("category", category.trim());
  const data = await request("/documents/upload", {
    method: "POST",
    body,
    signal,
  });
  if (data && Array.isArray(data.pages) && !data.document_id) {
    throw new Error(
      "The API is running the older PDF extraction backend. Restart the backend from this project's backend folder, then retry. This response does not confirm that the PDF was indexed for search.",
    );
  }
  if (
    !data ||
    typeof data.filename !== "string" ||
    typeof data.document_id !== "string" ||
    !data.document_id ||
    !count(data.total_pages) ||
    !count(data.total_chunks)
  ) {
    throw new Error(
      "The API returned an unexpected document format. Please check backend compatibility.",
    );
  }
  return data;
}

export async function searchDocuments(
  { query, limit = null, score_threshold = null, category, document_id = null },
  signal,
) {
  const data = await request("/search", {
    method: "POST",
    signal,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query: query.trim(),
      limit,
      score_threshold,
      category: category?.trim() || null,
      document_id,
    }),
  });
  if (
    !data ||
    typeof data.query !== "string" ||
    !count(data.total_results) ||
    !Array.isArray(data.results) ||
    data.total_results !== data.results.length ||
    !data.results.every(
      (result) =>
        result &&
        typeof result.id === "string" &&
        Number.isFinite(result.score) &&
        typeof result.text === "string" &&
        ["document_id", "source", "category"].every(
          (key) => result[key] == null || typeof result[key] === "string",
        ) &&
        (result.page_number == null ||
          (Number.isInteger(result.page_number) && result.page_number > 0)) &&
        (result.page_end == null ||
          (Number.isInteger(result.page_end) &&
            result.page_number != null &&
            result.page_end >= result.page_number)) &&
        (result.chunk_index == null || count(result.chunk_index)),
    )
  ) {
    throw new Error(
      "The API returned an unexpected search format. Please check backend compatibility.",
    );
  }
  return data;
}

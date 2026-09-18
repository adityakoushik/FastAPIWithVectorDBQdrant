# Current pipeline inspection

Application code and Qdrant data were not changed. Extraction and splitting were rerun with the current project classes; actual payloads were read using filtered Qdrant scroll, without vectors. Raw extraction and sentences are reconstructed from the original PDF, not historical snapshots from the original upload.

- Source: Employment_Agreement_Koushik Dutta_Full Stack Developer (IT).pdf
- Document ID: e9c2352a-062f-4f07-b7b1-c545cc480b49
- Collection: documents_v2
- 12 pages; 105 nonempty spaCy sentences; 83 reconstructed chunks; 83 stored chunks.
- Every reconstructed page number, chunk index and text matches the stored payload exactly.
- Settings: 500 characters per chunk, 1 sentence overlap when it fits, 50 characters overlap for oversized sentences.
- Chunk lengths: minimum 80, median 382, maximum 500 characters. 11 sentences exceed the budget.

## Confirmed broken-word origin

Page 10, sentence index 8 (zero-based), is 579 characters long. Raw extraction and spaCy preserve `may be asserted against`. The oversized fallback slices at offsets 0:500 and 450:579. Offset 450 is the final `y` in `may`, so stored chunk 71 starts `y be asserted against`. This is a chunk boundary defect, not missing PDF characters or a Qdrant mutation. See sentence_aware_chunker.py lines 183-206.

## Other observed quality issues

- The repeated footer occurs on all 12 pages and in 12 stored chunks. Page numbers and company footer are retained. Chunk 34 reproduces the screenshot's page 5 footer.
- Internal line breaks and indentation remain in sentences and chunks. They consume the character budget; stripping only removes outer whitespace.
- Page 5's confidentiality clause continues on page 6 (`business plans or client information...`). Chunking resets on every page, so page boundaries can also produce incomplete sentences.
- spaCy uses blank English plus a rule-based sentencizer. Sentence preservation is not equivalent to semantic/legal clause detection: chunk 73 ends with the next section number `14.`.
- One-sentence overlap is conditional: it is discarded when overlap plus the next sentence exceeds 500 characters. Oversized sentences use character overlap instead. There is no cross-page overlap.
- The current length distribution alone does not establish a good chunk budget. Clean extraction first, then inspect boundary integrity and retrieval again before selecting a new budget.

## Retrieval snapshot

POST to the existing localhost:8000/search endpoint, same screenshot query, same document ID, limit=10 and score_threshold=-1. No server defaults changed. search-top10.json includes full text, score, page and chunk index. The first three reproduce the screenshot: chunk 73 (0.592805), chunk 71 (0.5832336), chunk 34 (0.5708469).

## Files

- inspection.html: side-by-side raw pages, spaCy sentences and actual stored payloads; followed by full top-10 results.
- raw-pages.json: unmodified extracted page text.
- spacy-sentences.json: page-local sentence indexes, lengths and exact text.
- reconstructed-chunks.json: current chunker output.
- qdrant-chunks.json: actual stored text and metadata, without vectors.
- search-top10.json: diagnostic retrieval response.

Next implementation stage: conservative repeated-margin cleanup and whitespace normalization; then word-safe oversized splitting and an explicit page-boundary policy; finally rerun the same inspection and compare retrieval. No RAG was added.

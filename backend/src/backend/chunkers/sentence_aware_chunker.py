import re

from backend.chunkers.text_chunker import TextChunker
from backend.nlp.sentence_splitter import SentenceSplitter
from backend.schemas.document import DocumentChunk, DocumentPage


class SentenceAwareChunker(TextChunker):
    def __init__(self, sentence_splitter: SentenceSplitter, chunk_size: int = 500,
                 overlap_sentences: int = 1, oversized_overlap: int = 50):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if overlap_sentences < 0:
            raise ValueError("overlap_sentences cannot be negative")
        if not 0 <= oversized_overlap < chunk_size:
            raise ValueError("oversized_overlap must be nonnegative and smaller than chunk_size")
        self.sentence_splitter = sentence_splitter
        self.chunk_size = chunk_size
        self.overlap_sentences = overlap_sentences
        self.oversized_overlap = oversized_overlap

    def chunk(self, pages: list[DocumentPage]) -> list[DocumentChunk]:
        chunks = []
        for group in self._page_groups(pages):
            text = ""
            page_spans = []
            for page in group:
                if text:
                    text += " "
                start = len(text)
                text += " ".join(page.text.split())
                page_spans.append((start, len(text), page.page_number))

            def joined(units):
                # spaCy can place a boundary beside punctuation without a space.
                # Do not invent whitespace inside tokens such as `(Employee)`.
                return "".join(
                    (" " if i and units[i - 1][2] != unit[1] else "") + unit[0]
                    for i, unit in enumerate(units)
                )

            def append(units):
                if not units:
                    return
                first, last = units[0][1], units[-1][2]
                source_pages = [p for a, b, p in page_spans if a < last and b > first]
                chunks.append(DocumentChunk(
                    chunk_index=len(chunks), page_number=source_pages[0],
                    page_end=source_pages[-1] if len(source_pages) > 1 else None,
                    text=joined(units),
                ))

            current = []
            cursor = 0
            for sentence in self.sentence_splitter.split(text):
                sentence = sentence.strip()
                if not sentence:
                    continue
                start = text.find(sentence, cursor)
                if start < 0:
                    raise ValueError("Sentence splitter must preserve source text")
                end = start + len(sentence)
                cursor = end
                unit = (sentence, start, end)
                if len(sentence) > self.chunk_size:
                    append(current)
                    current = []
                    for a, b in self._oversized_spans(sentence):
                        append([(sentence[a:b], start + a, start + b)])
                    continue
                if current and len(joined([*current, unit])) > self.chunk_size:
                    append(current)
                    current = current[-self.overlap_sentences:] if self.overlap_sentences else []
                    while current and len(joined([*current, unit])) > self.chunk_size:
                        current.pop(0)
                current.append(unit)
            append(current)
        return chunks

    @staticmethod
    def _page_groups(pages):
        """Join only adjacent, nonempty pages with a likely sentence continuation.

        A lowercase opening is evidence of continuation; numbered/list headings,
        completed sentences and empty/missing pages remain hard boundaries.
        """
        group = []
        for page in pages:
            current = page.text.strip()
            previous = group[-1] if group else None
            continuation = (
                previous is not None and current and previous.text.strip()
                and page.page_number == previous.page_number + 1
                and current[0].islower()
                and not re.match(r"^(?:[a-z]|[ivxlcdm]+)[.)]\s", current)
                and not re.search(r'[.!?:][\)\]"\u201d\u2019]*$', previous.text.strip())
            )
            if not continuation and group:
                yield group
                group = []
            if current:
                group.append(page)
            elif group:
                yield group
                group = []
        if group:
            yield group

    def _oversized_spans(self, sentence):
        # Whole whitespace-delimited tokens are indivisible. A single token over
        # budget is emitted intact rather than corrupting a URL/identifier/word.
        words = list(re.finditer(r"\S+", sentence))
        i = 0
        while i < len(words):
            j = i + 1
            while j < len(words) and words[j].end() - words[i].start() <= self.chunk_size:
                j += 1
            yield words[i].start(), words[j - 1].end()
            if j == len(words):
                break
            next_i = j
            while (next_i > i + 1 and
                   words[j - 1].end() - words[next_i - 1].start() <= self.oversized_overlap):
                next_i -= 1
            # Overlap must leave space for at least one new token.
            while next_i < j and words[j].end() - words[next_i].start() > self.chunk_size:
                next_i += 1
            i = next_i

    def _split_oversized_sentence(self, sentence):
        return [sentence[a:b] for a, b in self._oversized_spans(sentence)]

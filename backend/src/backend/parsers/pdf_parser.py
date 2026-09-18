import math
import re
from collections import Counter

import pymupdf

from backend.parsers.document_parser import DocumentParser
from backend.schemas.document import DocumentPage


class PdfParser(DocumentParser):
    """Clean text PDFs conservatively; retain raw extraction for inspection."""

    def extract_raw_pages(self, file_bytes: bytes) -> list[DocumentPage]:
        with pymupdf.open(stream=file_bytes, filetype="pdf") as document:
            return [DocumentPage(page_number=i, text=page.get_text("text", sort=True))
                    for i, page in enumerate(document, 1)]

    def extract_pages(self, file_bytes: bytes) -> list[DocumentPage]:
        with pymupdf.open(stream=file_bytes, filetype="pdf") as document:
            pages = []
            repeated = Counter()
            for page in document:
                lines = []
                for block in page.get_text("dict")["blocks"]:
                    for line in block.get("lines", []):
                        text = "".join(span["text"] for span in line["spans"])
                        text = " ".join(text.split())
                        if not text:
                            continue
                        x0, y0, _, y1 = line["bbox"]
                        margin = ("top" if y1 < page.rect.height * .08 else
                                  "bottom" if y0 > page.rect.height * .92 else None)
                        lines.append((y0, x0, text, margin))
                lines.sort(key=lambda item: (round(item[0], 1), item[1]))
                pages.append(lines)
                repeated.update({(margin, text) for _, _, text, margin in lines if margin})

            threshold = max(2, math.ceil(len(pages) / 2))
            result = []
            for number, lines in enumerate(pages, 1):
                kept = []
                for _, _, text, margin in lines:
                    if margin and (self._is_page_number(text, number) or
                                   repeated[(margin, text)] >= threshold):
                        continue
                    kept.append(text)
                # Preserve visible hyphens: removing them blindly can change meaning.
                text = " ".join(" ".join(kept).replace("\u00ad", "").split())
                result.append(DocumentPage(page_number=number, text=text))
            return result

    @staticmethod
    def _is_page_number(text: str, number: int) -> bool:
        match = re.fullmatch(r"(?:page\s+)?(\d+)(?:\s*(?:of|/)\s*\d+)?", text, re.I)
        return bool(match and int(match[1]) == number)

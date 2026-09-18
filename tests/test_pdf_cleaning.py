import unittest
import pymupdf
from backend.parsers.pdf_parser import PdfParser


class PdfCleaningTests(unittest.TestCase):
    def make_pdf(self):
        with pymupdf.open() as pdf:
            for number in range(1, 4):
                page = pdf.new_page()
                page.insert_text((72, 35), "Repeated header")
                page.insert_text((72, 140), "Repeated header")
                page.insert_text((72, 180), "This sentence wraps")
                page.insert_text((72, 200), "across lines with   extra spaces.")
                page.insert_text((72, 240), "42")
                page.insert_text((72, 795), f"Page {number} of 3")
                page.insert_text((72, 815), "Confidential document")
                if number == 2:
                    page.insert_text((72, 770), "Unique body note")
            return pdf.tobytes()

    def test_margins_removed_body_preserved_and_raw_available(self):
        parser = PdfParser()
        data = self.make_pdf()
        raw = parser.extract_raw_pages(data)
        cleaned = parser.extract_pages(data)
        self.assertEqual(len(cleaned), 3)
        self.assertIn("Page 1 of 3", raw[0].text)
        for page in cleaned:
            self.assertEqual(page.text.count("Repeated header"), 1)
            self.assertNotIn("Confidential document", page.text)
            self.assertNotIn(f"Page {page.page_number} of 3", page.text)
            self.assertIn("42", page.text)
            self.assertIn("wraps across lines with extra spaces.", page.text)
            self.assertEqual(page.text, " ".join(page.text.split()))
        self.assertIn("Unique body note", cleaned[1].text)

    def test_unique_margin_and_single_page_content_are_preserved(self):
        with pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_text((72, 35), "Important title")
            page.insert_text((72, 200), "A well-known company.")
            page.insert_text((72, 815), "Unique legal note")
            data = pdf.tobytes()
        text = PdfParser().extract_pages(data)[0].text
        self.assertIn("Important title", text)
        self.assertIn("Unique legal note", text)
        self.assertIn("well-known", text)

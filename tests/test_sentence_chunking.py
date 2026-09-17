import unittest

from backend.chunkers.sentence_aware_chunker import SentenceAwareChunker
from backend.nlp.sentence_splitter import SentenceSplitter
from backend.nlp.spacy_sentence_splitter import SpacySentenceSplitter
from backend.schemas.document import DocumentPage


class StubSplitter(SentenceSplitter):
    def split(self, text: str) -> list[str]:
        return text.split("|") if text else []


class SentenceAwareChunkerTests(unittest.TestCase):
    def test_exact_budget_pages_and_indices(self):
        chunks = SentenceAwareChunker(
            StubSplitter(), 7, overlap_sentences=0, oversized_overlap=0,
        ).chunk([
            DocumentPage(page_number=2, text="abc|def|ghi"),
            DocumentPage(page_number=3, text=""),
            DocumentPage(page_number=4, text="xyz"),
        ])
        self.assertEqual([c.text for c in chunks], ["abc def", "ghi", "xyz"])
        self.assertEqual([c.page_number for c in chunks], [2, 2, 4])
        self.assertEqual([c.chunk_index for c in chunks], [0, 1, 2])

    def test_oversized_sentence_flushes_normal_sentences(self):
        chunks = SentenceAwareChunker(StubSplitter(), 5, oversized_overlap=2).chunk([
            DocumentPage(page_number=1, text="ab|abcdefgh|cd"),
        ])
        self.assertEqual([c.text for c in chunks], ["ab", "abcdefgh", "cd"])

    def test_sentence_overlap_stays_within_page(self):
        chunks = SentenceAwareChunker(StubSplitter(), 7, oversized_overlap=0).chunk([
            DocumentPage(page_number=2, text="abc|def|ghi|jkl"),
            DocumentPage(page_number=3, text=""),
            DocumentPage(page_number=4, text="xyz"),
        ])
        self.assertEqual([c.text for c in chunks], ["abc def", "def ghi", "ghi jkl", "xyz"])
        self.assertEqual([c.page_number for c in chunks], [2, 2, 2, 4])
        self.assertEqual([c.chunk_index for c in chunks], list(range(4)))

    def test_overlap_drops_oldest_sentences_to_fit(self):
        for count in (2, 100):
            with self.subTest(overlap_sentences=count):
                chunks = SentenceAwareChunker(
                    StubSplitter(), 11, overlap_sentences=count, oversized_overlap=0,
                ).chunk([DocumentPage(page_number=1, text="aaa|bbb|ccc|dddddd|eeeeeeeeeee")])
                self.assertEqual([c.text for c in chunks], [
                    "aaa bbb ccc", "ccc dddddd", "eeeeeeeeeee",
                ])

    def test_oversized_sentence_uses_whole_words_and_overlap(self):
        sentence = "alpha bravo charlie delta echo foxtrot golf hotel"
        chunks = SentenceAwareChunker(StubSplitter(), 24, oversized_overlap=8).chunk([
            DocumentPage(page_number=7, text=sentence),
        ])
        self.assertTrue(all(len(c.text) <= 24 for c in chunks))
        source_words = sentence.split()
        covered = set()
        for chunk in chunks:
            words = chunk.text.split()
            first = source_words.index(words[0])
            self.assertEqual(words, source_words[first:first + len(words)])
            covered.update(range(first, first + len(words)))
        self.assertEqual(covered, set(range(len(source_words))))
        self.assertEqual(chunks[0].text.split()[-1], chunks[1].text.split()[0])

    def test_indivisible_token_is_preserved_even_over_budget(self):
        text = "https://example.com/" + "a" * 600
        chunks = SentenceAwareChunker(StubSplitter()).chunk([
            DocumentPage(page_number=1, text=text),
        ])
        self.assertEqual([c.text for c in chunks], [text])

    def test_whitespace_and_empty_sentences_are_skipped(self):
        chunks = SentenceAwareChunker(StubSplitter()).chunk([
            DocumentPage(page_number=1, text=" |\t|\n"),
            DocumentPage(page_number=2, text="  abc  || def |"),
        ])
        self.assertEqual([c.model_dump() for c in chunks], [
            {"chunk_index": 0, "page_number": 2, "page_end": None, "text": "abc def"},
        ])

    def test_near_budget_overlap_still_makes_progress(self):
        chunks = SentenceAwareChunker(StubSplitter(), 7, oversized_overlap=6).chunk([
            DocumentPage(page_number=1, text="one two six ten"),
        ])
        self.assertEqual([c.text for c in chunks], ["one two", "two six", "six ten"])

    def test_invalid_overlap_configuration(self):
        for kwargs in (
            {"overlap_sentences": -1},
            {"oversized_overlap": -1},
            {"oversized_overlap": 500},
            {"oversized_overlap": 501},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                SentenceAwareChunker(StubSplitter(), **kwargs)

    def test_empty_input_and_invalid_budget(self):
        self.assertEqual(SentenceAwareChunker(StubSplitter()).chunk([]), [])
        for size in (0, -1):
            with self.subTest(size=size), self.assertRaises(ValueError):
                SentenceAwareChunker(StubSplitter(), size)


class SpacySentenceSplitterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.splitter = SpacySentenceSplitter()

    def test_empty_text(self):
        self.assertEqual(self.splitter.split(" \n\t"), [])

    def test_abbreviations_and_sentence_boundaries(self):
        self.assertEqual(
            self.splitter.split("Dr. Smith arrived. Are you ready? Let's go!"),
            ["Dr. Smith arrived.", "Are you ready?", "Let's go!"],
        )

    def test_cross_page_sentence_retains_page_range(self):
        chunks = SentenceAwareChunker(self.splitter).chunk([
            DocumentPage(page_number=5, text="Keep trade secrets, website information,"),
            DocumentPage(page_number=6, text="business plans confidential. Next sentence."),
        ])
        self.assertEqual(len(chunks), 1)
        self.assertIn("information, business plans", chunks[0].text)
        self.assertEqual((chunks[0].page_number, chunks[0].page_end), (5, 6))

    def test_completed_sentence_and_list_heading_do_not_join_pages(self):
        for first, second in [("Done.", "another paragraph."),
                              ("Unfinished clause", "b) New clause.")]:
            chunks = SentenceAwareChunker(self.splitter).chunk([
                DocumentPage(page_number=1, text=first),
                DocumentPage(page_number=2, text=second),
            ])
            self.assertEqual([c.page_number for c in chunks], [1, 2])
            self.assertTrue(all(c.page_end is None for c in chunks))

    def test_oversized_cross_page_parts_have_precise_source_pages(self):
        chunks = SentenceAwareChunker(self.splitter, 15, oversized_overlap=0).chunk([
            DocumentPage(page_number=1, text="alpha bravo"),
            DocumentPage(page_number=2, text="charlie delta echo."),
        ])
        self.assertEqual([c.text for c in chunks], ["alpha bravo", "charlie delta", "echo."])
        self.assertEqual([c.page_number for c in chunks], [1, 2, 2])
        self.assertTrue(all(c.page_end is None for c in chunks))

    def test_empty_or_missing_page_does_not_bridge_text(self):
        for pages in ([DocumentPage(page_number=2, text="")], []):
            chunks = SentenceAwareChunker(self.splitter).chunk([
                DocumentPage(page_number=1, text="Unfinished"), *pages,
                DocumentPage(page_number=3, text="continuation."),
            ])
            self.assertEqual([c.page_number for c in chunks], [1, 3])
            self.assertTrue(all(c.page_end is None for c in chunks))

    def test_real_pipeline_respects_whole_sentences(self):
        chunks = SentenceAwareChunker(self.splitter, 20, oversized_overlap=0).chunk([
            DocumentPage(page_number=1, text="First sentence. Second sentence. Third sentence."),
        ])
        self.assertEqual([c.text for c in chunks], [
            "First sentence.", "Second sentence.", "Third sentence.",
        ])

    def test_sentence_join_does_not_insert_space_inside_parentheses(self):
        text = "Signed. ____________________ ________________________ (Employee) (The Employer)"
        chunks = SentenceAwareChunker(self.splitter).chunk([
            DocumentPage(page_number=1, text=text),
        ])
        self.assertEqual([c.text for c in chunks], [text])


if __name__ == "__main__":
    unittest.main()

import spacy

from backend.nlp.sentence_splitter import SentenceSplitter


class SpacySentenceSplitter(SentenceSplitter):
    def __init__(self):
        self.nlp = spacy.blank("en")
        self.nlp.add_pipe("sentencizer")

    def split(self, text: str) -> list[str]:
        if not text.strip():
            return []
        document = self.nlp(text)
        return [
            sentence.text.strip()
            for sentence in document.sents
            if sentence.text.strip()
        ]

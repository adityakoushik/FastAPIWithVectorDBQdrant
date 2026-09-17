from abc import ABC, abstractmethod


class SentenceSplitter(ABC):
    @abstractmethod
    def split(self, text: str) -> list[str]:
        """Return sentences in their original order, omitting empty text."""
        pass

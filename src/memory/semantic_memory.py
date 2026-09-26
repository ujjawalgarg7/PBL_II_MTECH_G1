import json
from pathlib import Path


class SemanticMemory:
    """
    Stores stable facts and verified knowledge.

    Semantic memory is different from episodic memory:
    it stores facts rather than a sequence of events.
    """

    def __init__(self):
        self._facts = {}

    def add_fact(
        self,
        key,
        value,
        importance=0.5,
        source=None,
        verified=False,
    ):
        """
        Add or update a semantic fact.

        Args:
            key: Unique identifier for the fact.
            value: Fact content.
            importance: Importance score between 0 and 1.
            source: Where the fact came from.
            verified: Whether the fact has been verified.
        """

        if not key:
            raise ValueError("Fact key cannot be empty.")

        if value is None:
            raise ValueError("Fact value cannot be None.")

        if not 0 <= importance <= 1:
            raise ValueError(
                "Importance must be between 0 and 1."
            )

        self._facts[key] = {
            "key": key,
            "value": value,
            "importance": importance,
            "source": source,
            "verified": verified,
        }

    def get_fact(self, key):
        """Return a fact by its key."""

        return self._facts.get(key)

    def get_all(self):
        """Return all stored semantic facts."""

        return list(self._facts.values())

    def get_verified(self):
        """Return only verified facts."""

        return [
            fact
            for fact in self._facts.values()
            if fact["verified"]
        ]

    def get_important(self, threshold=0.7):
        """Return facts above the specified importance threshold."""

        return [
            fact
            for fact in self._facts.values()
            if fact["importance"] >= threshold
        ]

    def remove_fact(self, key):
        """Remove a fact if it exists."""

        self._facts.pop(key, None)

    def clear(self):
        """Remove all semantic facts."""

        self._facts.clear()

    def save(self, path):
        """Persist the current facts to a JSON file."""

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.get_all(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def load(self, path):
        """Replace current facts with those stored in a JSON file."""

        path = Path(path)
        facts = json.loads(path.read_text(encoding="utf-8"))

        if not isinstance(facts, list) or not all(
            isinstance(fact, dict) and fact.get("key")
            for fact in facts
        ):
            raise ValueError("Semantic memory JSON must contain fact objects with keys.")

        self._facts = {
            fact["key"]: fact
            for fact in facts
        }
        return self.get_all()

    def __len__(self):
        """Return the number of stored facts."""

        return len(self._facts)

import json
from pathlib import Path


class ShortTermMemory:
    """
    Stores recent information from the current agent interaction.

    Short-term memory has a fixed capacity. When the capacity is
    exceeded, the oldest item is removed.
    """

    def __init__(self, capacity=10):
        if capacity <= 0:
            raise ValueError("Capacity must be greater than zero.")

        self.capacity = capacity
        self._memory = []

    def add(self, item):
        """Add a new item to short-term memory."""

        self._memory.append(item)

        if len(self._memory) > self.capacity:
            self._memory.pop(0)

    def get_all(self):
        """Return all currently stored memory items."""

        return list(self._memory)

    def get_recent(self, count=1):
        """Return the most recent memory items."""

        if count <= 0:
            return []

        return self._memory[-count:]

    def clear(self):
        """Clear all short-term memory."""

        self._memory.clear()

    def save(self, path):
        """Persist the current memory items to a JSON file."""

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self._memory, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    def load(self, path):
        """Replace current memory items with those stored in a JSON file."""

        path = Path(path)
        items = json.loads(path.read_text(encoding="utf-8"))

        if not isinstance(items, list):
            raise ValueError("Short-term memory JSON must contain a list.")

        self._memory = items[-self.capacity:]
        return self.get_all()

    def __len__(self):
        """Return the number of stored memory items."""

        return len(self._memory)

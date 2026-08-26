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

    def __len__(self):
        """Return the number of stored memory items."""

        return len(self._memory)
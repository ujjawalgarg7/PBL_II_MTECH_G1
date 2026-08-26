from datetime import datetime


class EpisodicMemory:
    """
    Stores important events from previous interactions.

    Episodic memory preserves events that may be useful later
    during a long-running task.
    """

    def __init__(self, capacity=100):
        if capacity <= 0:
            raise ValueError("Capacity must be greater than zero.")

        self.capacity = capacity
        self._events = []

    def add_event(
        self,
        event,
        reason=None,
        importance=0.5,
        task_id=None,
    ):
        """
        Store an important event.

        Args:
            event: Description of the event.
            reason: Why the event is important.
            importance: Importance score between 0 and 1.
            task_id: Identifier of the current task.
        """

        if not event:
            raise ValueError("Event cannot be empty.")

        if not 0 <= importance <= 1:
            raise ValueError(
                "Importance must be between 0 and 1."
            )

        memory = {
            "event": event,
            "reason": reason,
            "importance": importance,
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
        }

        self._events.append(memory)

        if len(self._events) > self.capacity:
            self._events.pop(0)

    def get_all(self):
        """Return all stored episodic memories."""

        return list(self._events)

    def get_recent(self, count=1):
        """Return the most recent events."""

        if count <= 0:
            return []

        return self._events[-count:]

    def get_important(self, threshold=0.7):
        """
        Return memories whose importance is at or above
        the specified threshold.
        """

        return [
            event
            for event in self._events
            if event["importance"] >= threshold
        ]

    def get_by_task(self, task_id):
        """Return events belonging to a specific task."""

        if not task_id:
            return []

        return [
            event
            for event in self._events
            if event["task_id"] == task_id
        ]

    def clear(self):
        """Remove all episodic memories."""

        self._events.clear()

    def __len__(self):
        """Return the number of stored events."""

        return len(self._events)
import pytest

from src.memory.episodic_memory import EpisodicMemory


def test_add_event():
    memory = EpisodicMemory()

    memory.add_event(
        event="Previous patch failed.",
        reason="Regression test failed.",
        importance=0.9,
        task_id="debug_001",
    )

    events = memory.get_all()

    assert len(events) == 1
    assert events[0]["event"] == "Previous patch failed."
    assert events[0]["reason"] == "Regression test failed."
    assert events[0]["importance"] == 0.9
    assert events[0]["task_id"] == "debug_001"
    assert "timestamp" in events[0]


def test_recent_events():
    memory = EpisodicMemory()

    memory.add_event("First event")
    memory.add_event("Second event")
    memory.add_event("Third event")

    recent = memory.get_recent(2)

    assert len(recent) == 2
    assert recent[0]["event"] == "Second event"
    assert recent[1]["event"] == "Third event"


def test_important_events():
    memory = EpisodicMemory()

    memory.add_event(
        "Low importance event",
        importance=0.3,
    )

    memory.add_event(
        "Important event",
        importance=0.9,
    )

    important = memory.get_important(0.7)

    assert len(important) == 1
    assert important[0]["event"] == "Important event"


def test_events_by_task():
    memory = EpisodicMemory()

    memory.add_event(
        "Debugging event",
        task_id="debug_001",
    )

    memory.add_event(
        "Another debugging event",
        task_id="debug_001",
    )

    memory.add_event(
        "Different task",
        task_id="debug_002",
    )

    events = memory.get_by_task("debug_001")

    assert len(events) == 2


def test_capacity():
    memory = EpisodicMemory(capacity=2)

    memory.add_event("First")
    memory.add_event("Second")
    memory.add_event("Third")

    events = memory.get_all()

    assert len(events) == 2
    assert events[0]["event"] == "Second"
    assert events[1]["event"] == "Third"


def test_clear():
    memory = EpisodicMemory()

    memory.add_event("First")
    memory.add_event("Second")

    memory.clear()

    assert memory.get_all() == []


def test_invalid_importance():
    memory = EpisodicMemory()

    with pytest.raises(ValueError):
        memory.add_event(
            "Invalid event",
            importance=1.5,
        )


def test_empty_event():
    memory = EpisodicMemory()

    with pytest.raises(ValueError):
        memory.add_event("")
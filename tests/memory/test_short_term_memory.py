import pytest

from src.memory.short_term_memory import ShortTermMemory


def test_add_and_retrieve_memory():
    memory = ShortTermMemory()

    memory.add("User requested bug analysis.")

    assert memory.get_all() == [
        "User requested bug analysis."
    ]


def test_recent_memory():
    memory = ShortTermMemory()

    memory.add("First")
    memory.add("Second")
    memory.add("Third")

    assert memory.get_recent(2) == [
        "Second",
        "Third"
    ]


def test_memory_capacity():
    memory = ShortTermMemory(capacity=3)

    memory.add("First")
    memory.add("Second")
    memory.add("Third")
    memory.add("Fourth")

    assert memory.get_all() == [
        "Second",
        "Third",
        "Fourth"
    ]


def test_clear_memory():
    memory = ShortTermMemory()

    memory.add("First")
    memory.add("Second")

    memory.clear()

    assert memory.get_all() == []


def test_invalid_capacity():
    with pytest.raises(ValueError):
        ShortTermMemory(capacity=0)


def test_save_and_load_memory(tmp_path):
    saved_path = tmp_path / "short_term.json"
    memory = ShortTermMemory(capacity=2)
    memory.add("First")
    memory.add("Second")
    memory.save(saved_path)

    restored = ShortTermMemory(capacity=2)
    restored.load(saved_path)

    assert restored.get_all() == ["First", "Second"]

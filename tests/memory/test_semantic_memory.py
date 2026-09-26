import pytest

from src.memory.semantic_memory import SemanticMemory


def test_add_and_get_fact():
    memory = SemanticMemory()

    memory.add_fact(
        key="database",
        value="The project uses PostgreSQL.",
    )

    fact = memory.get_fact("database")

    assert fact["value"] == "The project uses PostgreSQL."


def test_update_fact():
    memory = SemanticMemory()

    memory.add_fact(
        key="database",
        value="The project uses MySQL.",
    )

    memory.add_fact(
        key="database",
        value="The project uses PostgreSQL.",
    )

    fact = memory.get_fact("database")

    assert fact["value"] == "The project uses PostgreSQL."
    assert len(memory) == 1


def test_verified_facts():
    memory = SemanticMemory()

    memory.add_fact(
        key="verified_fact",
        value="Python version is 3.11.",
        verified=True,
    )

    memory.add_fact(
        key="unverified_fact",
        value="The project may use Redis.",
        verified=False,
    )

    verified = memory.get_verified()

    assert len(verified) == 1
    assert verified[0]["key"] == "verified_fact"


def test_important_facts():
    memory = SemanticMemory()

    memory.add_fact(
        key="low",
        value="Low importance fact.",
        importance=0.3,
    )

    memory.add_fact(
        key="high",
        value="High importance fact.",
        importance=0.9,
    )

    important = memory.get_important(0.7)

    assert len(important) == 1
    assert important[0]["key"] == "high"


def test_remove_fact():
    memory = SemanticMemory()

    memory.add_fact(
        key="database",
        value="PostgreSQL",
    )

    memory.remove_fact("database")

    assert memory.get_fact("database") is None
    assert len(memory) == 0


def test_clear():
    memory = SemanticMemory()

    memory.add_fact(
        key="one",
        value="Fact one",
    )

    memory.add_fact(
        key="two",
        value="Fact two",
    )

    memory.clear()

    assert memory.get_all() == []


def test_invalid_importance():
    memory = SemanticMemory()

    with pytest.raises(ValueError):
        memory.add_fact(
            key="test",
            value="Invalid",
            importance=1.5,
        )


def test_empty_key():
    memory = SemanticMemory()

    with pytest.raises(ValueError):
        memory.add_fact(
            key="",
            value="Something",
        )


def test_save_and_load_facts(tmp_path):
    saved_path = tmp_path / "semantic.json"
    memory = SemanticMemory()
    memory.add_fact("database", "PostgreSQL", verified=True)
    memory.save(saved_path)

    restored = SemanticMemory()
    restored.load(saved_path)

    assert restored.get_fact("database") == memory.get_fact("database")

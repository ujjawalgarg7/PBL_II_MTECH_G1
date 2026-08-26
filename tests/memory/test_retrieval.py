from src.memory.short_term_memory import ShortTermMemory
from src.memory.episodic_memory import EpisodicMemory
from src.memory.semantic_memory import SemanticMemory
from src.retrieval.retrieval import MemoryRetriever


def create_retriever():
    short_term = ShortTermMemory()

    episodic = EpisodicMemory()

    semantic = SemanticMemory()

    return (
        short_term,
        episodic,
        semantic,
        MemoryRetriever(
            short_term,
            episodic,
            semantic,
        ),
    )


def test_retrieve_short_term_memory():

    short_term, episodic, semantic, retriever = (
        create_retriever()
    )

    short_term.add(
        "The current bug is related to database connection."
    )

    results = retriever.retrieve("database")

    assert len(results) == 1
    assert results[0]["memory_type"] == "short_term"


def test_retrieve_episodic_memory():

    short_term, episodic, semantic, retriever = (
        create_retriever()
    )

    episodic.add_event(
        event="Previous database patch failed.",
        reason="Database connection test failed.",
        importance=0.9,
        task_id="debug_001",
    )

    results = retriever.retrieve("database")

    assert len(results) == 1
    assert results[0]["memory_type"] == "episodic"


def test_retrieve_semantic_memory():

    short_term, episodic, semantic, retriever = (
        create_retriever()
    )

    semantic.add_fact(
        key="database",
        value="The project uses PostgreSQL.",
        verified=True,
    )

    results = retriever.retrieve("PostgreSQL")

    assert len(results) == 1
    assert results[0]["memory_type"] == "semantic"


def test_retrieve_from_all_memory_layers():

    short_term, episodic, semantic, retriever = (
        create_retriever()
    )

    short_term.add(
        "PostgreSQL connection is currently failing."
    )

    episodic.add_event(
        event="Previous PostgreSQL fix failed.",
        reason="Connection test failed.",
        task_id="debug_001",
    )

    semantic.add_fact(
        key="database",
        value="The project uses PostgreSQL.",
    )

    results = retriever.retrieve("PostgreSQL")

    assert len(results) == 3

    memory_types = {
        result["memory_type"]
        for result in results
    }

    assert memory_types == {
        "short_term",
        "episodic",
        "semantic",
    }


def test_no_results_for_unknown_query():

    short_term, episodic, semantic, retriever = (
        create_retriever()
    )

    short_term.add("Python debugging")

    results = retriever.retrieve("JavaScript")

    assert results == []


def test_empty_query():

    short_term, episodic, semantic, retriever = (
        create_retriever()
    )

    results = retriever.retrieve("")

    assert results == []
def test_memory_score_is_present():

    short_term, episodic, semantic, retriever = (
        create_retriever()
    )

    semantic.add_fact(
        key="database",
        value="The project uses PostgreSQL.",
        importance=0.9,
    )

    results = retriever.retrieve("PostgreSQL")

    assert len(results) == 1

    result = results[0]

    assert "similarity" in result
    assert "recency" in result
    assert "importance" in result
    assert "consistency" in result
    assert "score" in result


def test_results_are_ranked():

    short_term, episodic, semantic, retriever = (
        create_retriever()
    )

    semantic.add_fact(
        key="database",
        value="PostgreSQL database",
        importance=0.2,
    )

    semantic.add_fact(
        key="database_important",
        value="PostgreSQL database",
        importance=0.9,
    )

    results = retriever.retrieve("PostgreSQL")

    assert len(results) == 2

    assert (
        results[0]["score"]
        >= results[1]["score"]
    )


def test_task_consistency_affects_score():

    short_term, episodic, semantic, retriever = (
        create_retriever()
    )

    episodic.add_event(
        event="Previous PostgreSQL connection failed.",
        importance=0.5,
        task_id="debug_001",
    )

    episodic.add_event(
        event="Previous PostgreSQL connection failed.",
        importance=0.5,
        task_id="debug_002",
    )

    results = retriever.retrieve(
        "PostgreSQL",
        task_id="debug_001",
    )

    assert len(results) == 2

    assert (
        results[0]["content"]["task_id"]
        == "debug_001"
    )


def test_invalid_weights():

    short_term = ShortTermMemory()
    episodic = EpisodicMemory()
    semantic = SemanticMemory()

    try:
        MemoryRetriever(
            short_term,
            episodic,
            semantic,
            alpha=-1,
        )

        assert False

    except ValueError:
        assert True


def test_score_range():

    short_term, episodic, semantic, retriever = (
        create_retriever()
    )

    semantic.add_fact(
        key="database",
        value="PostgreSQL",
        importance=0.9,
    )

    results = retriever.retrieve("PostgreSQL")

    assert len(results) == 1

    assert 0 <= results[0]["score"] <= 1
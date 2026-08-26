from pathlib import Path

from src.agent.repository_agent import RepositoryAgent


def get_test_repository():
    """
    Locate the existing test_files directory.
    """

    return (
        Path(__file__).resolve().parents[2]
        / "test_files"
    )


def test_agent_initialization():

    repository = get_test_repository()

    agent = RepositoryAgent(repository)

    assert agent.repository_path == repository

    assert agent.ingestor is not None
    assert agent.parser is not None
    assert agent.ast_search is not None
    assert agent.code_search is not None

    assert agent.short_term_memory is not None
    assert agent.episodic_memory is not None
    assert agent.semantic_memory is not None
    assert agent.memory_retriever is not None


def test_repository_summary():

    repository = get_test_repository()

    agent = RepositoryAgent(repository)

    summary = agent.repository_summary()

    assert "repository_name" in summary
    assert "repository_path" in summary
    assert "total_files" in summary
    assert "file_types" in summary


def test_search_code():

    repository = get_test_repository()

    agent = RepositoryAgent(repository)

    results = agent.search_code(
        "Calculator"
    )

    assert isinstance(results, list)


def test_search_symbol():

    repository = get_test_repository()

    agent = RepositoryAgent(repository)

    results = agent.search_symbol(
        "Calculator"
    )

    assert isinstance(results, list)


def test_find_classes():

    repository = get_test_repository()

    agent = RepositoryAgent(repository)

    results = agent.find_classes()

    assert isinstance(results, list)


def test_find_functions():

    repository = get_test_repository()

    agent = RepositoryAgent(repository)

    results = agent.find_functions()

    assert isinstance(results, list)


def test_find_methods():

    repository = get_test_repository()

    agent = RepositoryAgent(repository)

    results = agent.find_methods()

    assert isinstance(results, list)


def test_remember_event():

    repository = get_test_repository()

    agent = RepositoryAgent(repository)

    agent.remember_event(
        event="Test failure detected.",
        reason="Regression test failed.",
        importance=0.9,
        task_id="debug_001",
    )

    events = agent.episodic_memory.get_all()

    assert len(events) == 1

    assert (
        events[0]["event"]
        == "Test failure detected."
    )


def test_remember_fact():

    repository = get_test_repository()

    agent = RepositoryAgent(repository)

    agent.remember_fact(
        key="language",
        value="Python",
        importance=0.9,
        verified=True,
    )

    fact = agent.semantic_memory.get_fact(
        "language"
    )

    assert fact["value"] == "Python"
    assert fact["verified"] is True


def test_retrieve_memory():

    repository = get_test_repository()

    agent = RepositoryAgent(repository)

    agent.remember_fact(
        key="language",
        value="Python is used by this project.",
    )

    results = agent.retrieve_memory(
        "Python"
    )

    assert len(results) == 1

    assert results[0]["memory_type"] == "semantic"
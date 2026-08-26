from src.code_search.ast_search import ASTSearch


def create_test_repository(tmp_path):

    repository = tmp_path / "sample_repo"

    src = repository / "src"
    src.mkdir(parents=True)

    (src / "database.py").write_text(
        """
import sqlite3
from pathlib import Path


class Database:

    def connect(self):
        return sqlite3.connect("test.db")

    def close(self):
        pass


def create_database():
    database = Database()
    database.connect()
    return database
""",
        encoding="utf-8"
    )

    (src / "utils.py").write_text(
        """
import os


def calculate_total(values):
    return sum(values)


def connect():
    pass
""",
        encoding="utf-8"
    )

    return repository


def test_find_classes(tmp_path):

    repository = create_test_repository(tmp_path)

    search = ASTSearch(repository)

    results = search.find_classes()

    assert len(results) == 1
    assert results[0]["name"] == "Database"


def test_find_functions(tmp_path):

    repository = create_test_repository(tmp_path)

    search = ASTSearch(repository)

    results = search.find_functions()

    names = [result["name"] for result in results]

    assert "create_database" in names
    assert "calculate_total" in names
    assert "connect" in names


def test_find_methods(tmp_path):

    repository = create_test_repository(tmp_path)

    search = ASTSearch(repository)

    results = search.find_methods()

    methods = [
        result["method"]
        for result in results
    ]

    assert "connect" in methods
    assert "close" in methods

    assert any(
        result["class"] == "Database"
        and result["method"] == "connect"
        for result in results
    )


def test_find_imports(tmp_path):

    repository = create_test_repository(tmp_path)

    search = ASTSearch(repository)

    results = search.find_imports()

    modules = [
        result["module"]
        for result in results
    ]

    assert "sqlite3" in modules
    assert "pathlib" in modules
    assert "os" in modules


def test_find_function_calls(tmp_path):

    repository = create_test_repository(tmp_path)

    search = ASTSearch(repository)

    results = search.find_function_calls("connect")

    assert len(results) >= 1

    assert any(
        result["file"].endswith("database.py")
        for result in results
    )


def test_find_class_methods(tmp_path):

    repository = create_test_repository(tmp_path)

    search = ASTSearch(repository)

    results = search.find_class_methods("Database")

    methods = [
        result["method"]
        for result in results
    ]

    assert "connect" in methods
    assert "close" in methods
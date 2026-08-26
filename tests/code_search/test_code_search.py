from src.code_search.code_search import CodeSearch


def create_test_repository(tmp_path):

    repository = tmp_path / "sample_repo"

    src = repository / "src"
    utils = src / "utils"

    utils.mkdir(parents=True)

    (src / "database.py").write_text(
        """
import sqlite3


class Database:

    def connect(self):
        return sqlite3.connect("test.db")


def create_database():
    return Database()
""",
        encoding="utf-8"
    )

    (utils / "helpers.py").write_text(
        """
def calculate_total(values):
    return sum(values)


def format_result(value):
    return str(value)
""",
        encoding="utf-8"
    )

    return repository


def test_get_source_files(tmp_path):

    repository = create_test_repository(tmp_path)

    search = CodeSearch(repository)

    files = search.get_source_files()

    assert len(files) == 2


def test_search_text(tmp_path):

    repository = create_test_repository(tmp_path)

    search = CodeSearch(repository)

    results = search.search_text("sqlite3")

    assert len(results) >= 1

    assert any(
        result["file"].endswith("database.py")
        for result in results
    )


def test_search_symbol(tmp_path):

    repository = create_test_repository(tmp_path)

    search = CodeSearch(repository)

    results = search.search_symbol("Database")

    assert len(results) == 1

    assert results[0]["name"] == "Database"
    assert results[0]["type"] == "class"


def test_search_class(tmp_path):

    repository = create_test_repository(tmp_path)

    search = CodeSearch(repository)

    results = search.search_class("Database")

    assert len(results) == 1
    assert results[0]["type"] == "class"


def test_search_function(tmp_path):

    repository = create_test_repository(tmp_path)

    search = CodeSearch(repository)

    results = search.search_function("calculate_total")

    assert len(results) == 1
    assert results[0]["name"] == "calculate_total"


def test_search_file(tmp_path):

    repository = create_test_repository(tmp_path)

    search = CodeSearch(repository)

    results = search.search_file("database.py")

    assert len(results) == 1
    assert results[0].endswith("database.py")
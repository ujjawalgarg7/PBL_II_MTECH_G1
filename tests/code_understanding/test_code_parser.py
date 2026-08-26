from pathlib import Path

from src.code_understanding.code_parser import CodeParser


def create_test_repository(tmp_path):
    repository = tmp_path / "sample_repo"

    src = repository / "src"
    src.mkdir(parents=True)

    file_path = src / "example.py"

    file_path.write_text(
        """
import os
from pathlib import Path


class Calculator:

    def add(self, a, b):
        return a + b


def multiply(a, b):
    return a * b
""",
        encoding="utf-8"
    )

    return repository


def test_get_source_files(tmp_path):
    repository = create_test_repository(tmp_path)

    parser = CodeParser(repository)

    files = parser.get_source_files()

    assert len(files) == 1
    assert files[0].name == "example.py"


def test_parse_file(tmp_path):
    repository = create_test_repository(tmp_path)

    parser = CodeParser(repository)

    file_path = repository / "src" / "example.py"

    tree = parser.parse_file(file_path)

    assert tree is not None


def test_extract_symbols(tmp_path):
    repository = create_test_repository(tmp_path)

    parser = CodeParser(repository)

    file_path = repository / "src" / "example.py"

    result = parser.extract_symbols(file_path)

    assert "Calculator" in [
        item["name"] for item in result["classes"]
    ]

    assert "multiply" in [
        item["name"] for item in result["functions"]
    ]

    assert len(result["imports"]) == 2


def test_analyze_repository(tmp_path):
    repository = create_test_repository(tmp_path)

    parser = CodeParser(repository)

    result = parser.analyze_repository()

    assert len(result) == 1
    assert result[0]["file"].endswith("example.py")
def test_extract_methods():

    file_path = (
        Path(__file__).resolve().parents[2]
        / "test_files"
        / "sample.py"
    )

    parser = CodeParser(file_path)

    symbols = parser.extract_symbols(file_path)

    assert {
        "class": "Calculator",
        "name": "square",
        "line": 8
    } in symbols["methods"]
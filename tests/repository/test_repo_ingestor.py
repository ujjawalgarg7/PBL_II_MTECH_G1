from pathlib import Path

from src.repository.repo_ingestor import RepositoryIngestor


def test_repository_validation():

    repository_path = Path(__file__).resolve().parents[2]

    ingestor = RepositoryIngestor(repository_path)

    assert ingestor.validate() is True


def test_repository_scan():

    repository_path = Path(__file__).resolve().parents[2]

    ingestor = RepositoryIngestor(repository_path)

    files = ingestor.scan()

    assert isinstance(files, list)


def test_repository_structure():

    repository_path = Path(__file__).resolve().parents[2]

    ingestor = RepositoryIngestor(repository_path)

    structure = ingestor.get_structure()

    assert isinstance(structure, list)


def test_repository_summary():

    repository_path = Path(__file__).resolve().parents[2]

    ingestor = RepositoryIngestor(repository_path)

    summary = ingestor.summary()

    assert summary["repository_name"] == repository_path.name

    assert "total_files" in summary

    assert "file_types" in summary
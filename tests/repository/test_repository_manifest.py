from pathlib import Path

from src.repository.repository_manifest import RepositoryManifest


def test_manifest_build():

    repository_path = Path(__file__).resolve().parents[2]

    manifest = RepositoryManifest(repository_path)

    result = manifest.build()

    assert "repository_name" in result
    assert "repository_path" in result
    assert "total_files" in result
    assert "files" in result

    assert isinstance(result["files"], list)


def test_manifest_file_records():

    repository_path = Path(__file__).resolve().parents[2]

    manifest = RepositoryManifest(repository_path)

    result = manifest.build()

    if result["files"]:

        file_record = result["files"][0]

        assert "name" in file_record
        assert "path" in file_record
        assert "extension" in file_record
        assert "size_bytes" in file_record
        assert "file_type" in file_record


def test_manifest_statistics():

    repository_path = Path(__file__).resolve().parents[2]

    manifest = RepositoryManifest(repository_path)

    statistics = manifest.statistics()

    assert "source_files" in statistics
    assert "test_files" in statistics
    assert "documentation_files" in statistics
    assert "configuration_files" in statistics
    assert "other_files" in statistics
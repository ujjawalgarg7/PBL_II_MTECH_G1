from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class FileRecord:
    """Information about one file in a repository."""

    name: str
    path: str
    extension: str
    size_bytes: int
    file_type: str


class RepositoryManifest:
    """
    Creates a structured manifest of a repository.

    The manifest is designed to be consumed later by:
    - Code Understanding
    - AST / Code Search
    - Memory
    - Retrieval
    """

    SOURCE_EXTENSIONS = {
        ".py",
        ".java",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".cs",
        ".go",
        ".rs",
    }

    TEST_NAME_PATTERNS = {
        "test_",
        "_test",
        "tests",
    }

    def __init__(self, repository_path):
        self.repository_path = Path(repository_path).resolve()

    def _classify_file(self, path: Path) -> str:
        """
        Classify a file as source, test, configuration,
        documentation, or other.
        """

        name = path.name.lower()
        extension = path.suffix.lower()

        # Test files
        if (
            name.startswith("test_")
            or name.endswith("_test.py")
            or "tests" in path.parts
        ):
            return "test"

        # Source files
        if extension in self.SOURCE_EXTENSIONS:
            return "source"

        # Documentation
        if extension in {".md", ".rst", ".txt"}:
            return "documentation"

        # Configuration
        if extension in {
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".xml",
        }:
            return "configuration"

        return "other"

    def build(self):
        """
        Build the complete repository manifest.
        """

        files = []

        for path in self.repository_path.rglob("*"):

            if not path.is_file():
                continue

            if any(
                ignored in path.parts
                for ignored in {
                    ".git",
                    "__pycache__",
                    ".venv",
                    "venv",
                    "node_modules",
                    ".idea",
                    ".vscode",
                    "build",
                    "dist",
                }
            ):
                continue

            relative_path = path.relative_to(self.repository_path)

            record = FileRecord(
                name=path.name,
                path=str(relative_path),
                extension=path.suffix.lower(),
                size_bytes=path.stat().st_size,
                file_type=self._classify_file(path),
            )

            files.append(record)

        return {
            "repository_name": self.repository_path.name,
            "repository_path": str(self.repository_path),
            "total_files": len(files),
            "files": [
                asdict(file)
                for file in files
            ],
        }

    def statistics(self):
        """
        Return basic statistics about the repository.
        """

        manifest = self.build()

        statistics = {
            "source_files": 0,
            "test_files": 0,
            "documentation_files": 0,
            "configuration_files": 0,
            "other_files": 0,
        }

        for file in manifest["files"]:

            file_type = file["file_type"]

            if file_type == "source":
                statistics["source_files"] += 1

            elif file_type == "test":
                statistics["test_files"] += 1

            elif file_type == "documentation":
                statistics["documentation_files"] += 1

            elif file_type == "configuration":
                statistics["configuration_files"] += 1

            else:
                statistics["other_files"] += 1

        return statistics
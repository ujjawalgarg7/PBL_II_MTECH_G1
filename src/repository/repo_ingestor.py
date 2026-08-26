from pathlib import Path


class RepositoryIngestor:
    """
    Ingests any local software repository or folder.

    The repository path is provided by the user.
    The ingestor recursively discovers folders and files.
    """

    IGNORED_DIRECTORIES = {
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

    def __init__(self, repository_path):
        self.repository_path = Path(repository_path).resolve()

    def validate(self):
        """Check whether the supplied path is a valid directory."""

        if not self.repository_path.exists():
            raise ValueError(
                f"Repository does not exist: {self.repository_path}"
            )

        if not self.repository_path.is_dir():
            raise ValueError(
                f"Repository path is not a directory: {self.repository_path}"
            )

        return True

    def scan(self):
        """
        Recursively scan the repository.

        Returns:
            list[dict]: Information about discovered files.
        """

        self.validate()

        files = []

        for path in self.repository_path.rglob("*"):

            if not path.is_file():
                continue

            # Ignore files inside unwanted directories.
            if any(
                ignored in path.parts
                for ignored in self.IGNORED_DIRECTORIES
            ):
                continue

            relative_path = path.relative_to(self.repository_path)

            files.append(
                {
                    "name": path.name,
                    "path": str(relative_path),
                    "extension": path.suffix.lower(),
                    "size_bytes": path.stat().st_size,
                }
            )

        return files

    def get_structure(self):
        """
        Return the complete repository structure.
        """

        self.validate()

        structure = []

        for path in self.repository_path.rglob("*"):

            if any(
                ignored in path.parts
                for ignored in self.IGNORED_DIRECTORIES
            ):
                continue

            relative_path = path.relative_to(self.repository_path)

            structure.append(
                {
                    "path": str(relative_path),
                    "type": "directory" if path.is_dir() else "file",
                }
            )

        return sorted(
            structure,
            key=lambda item: item["path"]
        )

    def summary(self):
        """
        Return a high-level repository summary.
        """

        files = self.scan()

        extensions = {}

        for file in files:
            extension = file["extension"] or "[no extension]"

            extensions[extension] = (
                extensions.get(extension, 0) + 1
            )

        return {
            "repository_name": self.repository_path.name,
            "repository_path": str(self.repository_path),
            "total_files": len(files),
            "file_types": extensions,
        }
from pathlib import Path
import ast


class CodeSearch:
    """Search source code across any local repository or folder."""

    SUPPORTED_EXTENSIONS = {".py"}

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

        if not self.repository_path.exists():
            raise FileNotFoundError(
                f"Repository path does not exist: {self.repository_path}"
            )

        if not self.repository_path.is_dir():
            raise NotADirectoryError(
                f"Repository path is not a directory: {self.repository_path}"
            )

    def get_source_files(self):
        """Return all supported Python source files."""

        files = []

        for path in self.repository_path.rglob("*"):

            if not path.is_file():
                continue

            # Ignore unwanted directories
            if any(
                ignored in path.parts
                for ignored in self.IGNORED_DIRECTORIES
            ):
                continue

            # Only supported source files
            if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
                continue

            files.append(path)

        return sorted(files)

    def search_text(self, query):
        """
        Search for text inside source files.

        Returns:
            list[dict]: Matching files, line numbers and content.
        """

        if not query:
            return []

        query = query.lower()
        results = []

        for file_path in self.get_source_files():

            try:
                lines = file_path.read_text(
                    encoding="utf-8",
                    errors="ignore"
                ).splitlines()

            except OSError:
                continue

            for line_number, line in enumerate(
                lines,
                start=1
            ):

                if query in line.lower():

                    results.append({
                        "file": str(file_path),
                        "line": line_number,
                        "content": line.strip()
                    })

        return results

    def search_symbol(self, symbol_name):
        """
        Search for classes and functions with a given name.

        Returns:
            list[dict]: Matching symbols.
        """

        if not symbol_name:
            return []

        results = []

        for file_path in self.get_source_files():

            try:
                source = file_path.read_text(
                    encoding="utf-8",
                    errors="ignore"
                )

                tree = ast.parse(source)

            except (OSError, SyntaxError):
                continue

            for node in ast.walk(tree):

                if isinstance(
                    node,
                    (
                        ast.FunctionDef,
                        ast.AsyncFunctionDef,
                        ast.ClassDef
                    )
                ):

                    if node.name != symbol_name:
                        continue

                    if isinstance(
                        node,
                        ast.ClassDef
                    ):
                        symbol_type = "class"
                    else:
                        symbol_type = "function"

                    results.append({
                        "name": node.name,
                        "type": symbol_type,
                        "file": str(file_path),
                        "line": node.lineno
                    })

        return results

    def search_class(self, class_name):
        """Search specifically for classes."""

        return [
            result
            for result in self.search_symbol(class_name)
            if result["type"] == "class"
        ]

    def search_function(self, function_name):
        """Search specifically for functions."""

        return [
            result
            for result in self.search_symbol(function_name)
            if result["type"] == "function"
        ]

    def search_file(self, filename):
        """Find Python files by filename."""

        if not filename:
            return []

        filename = filename.lower()

        return [
            str(path)
            for path in self.get_source_files()
            if filename in path.name.lower()
        ]
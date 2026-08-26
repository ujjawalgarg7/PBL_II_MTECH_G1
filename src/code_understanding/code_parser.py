from pathlib import Path
import ast


class CodeParser:
    """Parse Python files and extract structural information."""

    SUPPORTED_EXTENSIONS = {".py"}

    def __init__(self, repository_path):
        self.repository_path = Path(repository_path).resolve()

        if not self.repository_path.exists():
            raise FileNotFoundError(
                f"Repository path does not exist: {self.repository_path}"
            )

        if not (
            self.repository_path.is_dir()
            or (
                self.repository_path.is_file()
                and self.repository_path.suffix.lower()
                in self.SUPPORTED_EXTENSIONS
            )
        ):
            raise NotADirectoryError(
                f"Repository path is not a directory or supported file: "
                f"{self.repository_path}"
            )

    def get_source_files(self):
        """Return all supported Python source files."""

        # If user supplied a single Python file
        if self.repository_path.is_file():
            return [self.repository_path]

        # If user supplied a repository/folder
        files = []

        for path in self.repository_path.rglob("*"):
            if not path.is_file():
                continue

            if path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                files.append(path)

        return sorted(files)

    def parse_file(self, file_path):
        """Parse one Python file and return its AST."""

        file_path = Path(file_path)

        source = file_path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        return ast.parse(source)

    def extract_symbols(self, file_path):
        """Extract classes, functions, methods and imports."""

        tree = self.parse_file(file_path)

        symbols = {
            "file": str(file_path),
            "classes": [],
            "functions": [],
            "methods": [],
            "imports": []
        }

        # Walk through the complete AST
        for node in ast.walk(tree):

            # -----------------------------
            # Classes
            # -----------------------------
            if isinstance(node, ast.ClassDef):

                symbols["classes"].append({
                    "name": node.name,
                    "line": node.lineno
                })

                # Extract methods directly inside this class
                for child in node.body:

                    if isinstance(
                        child,
                        (ast.FunctionDef, ast.AsyncFunctionDef)
                    ):
                        symbols["methods"].append({
                            "class": node.name,
                            "name": child.name,
                            "line": child.lineno
                        })

            # -----------------------------
            # Top-level functions
            # -----------------------------
            elif isinstance(node, ast.FunctionDef):

                if not self._is_method(tree, node):
                    symbols["functions"].append({
                        "name": node.name,
                        "line": node.lineno
                    })

            # -----------------------------
            # Top-level async functions
            # -----------------------------
            elif isinstance(node, ast.AsyncFunctionDef):

                if not self._is_method(tree, node):
                    symbols["functions"].append({
                        "name": node.name,
                        "line": node.lineno
                    })

            # -----------------------------
            # Imports
            # -----------------------------
            elif isinstance(
                node,
                (ast.Import, ast.ImportFrom)
            ):
                symbols["imports"].append(
                    self._get_import_name(node)
                )

        return symbols

    def _is_method(self, tree, target):
        """Check whether a function node belongs directly to a class."""

        for node in ast.walk(tree):

            if isinstance(node, ast.ClassDef):

                for child in node.body:

                    if child is target:
                        return True

        return False

    def _get_import_name(self, node):
        """Convert an AST import node into a readable string."""

        if isinstance(node, ast.Import):

            return ", ".join(
                alias.name
                for alias in node.names
            )

        if isinstance(node, ast.ImportFrom):

            module = node.module or ""

            names = ", ".join(
                alias.name
                for alias in node.names
            )

            return f"{module}: {names}"

        return ""

    def analyze_repository(self):
        """Analyze all supported Python source files."""

        result = []

        for file_path in self.get_source_files():

            try:
                result.append(
                    self.extract_symbols(file_path)
                )

            except SyntaxError as error:

                result.append({
                    "file": str(file_path),
                    "error": "SyntaxError",
                    "message": str(error)
                })

        return result
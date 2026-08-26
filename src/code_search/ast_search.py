from pathlib import Path
import ast


class ASTSearch:
    """Perform structural searches using Python's AST."""

    SUPPORTED_EXTENSIONS = {".py"}

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
        """Return all supported source files recursively."""

        return sorted(
            path
            for path in self.repository_path.rglob("*")
            if path.is_file()
            and path.suffix.lower() in self.SUPPORTED_EXTENSIONS
        )

    def _parse_file(self, file_path):
        """Parse a Python file into an AST."""

        try:
            source = Path(file_path).read_text(
                encoding="utf-8",
                errors="ignore"
            )

            return ast.parse(source)

        except (OSError, SyntaxError):
            return None

    def find_classes(self):
        """Find every class in the repository."""

        results = []

        for file_path in self.get_source_files():

            tree = self._parse_file(file_path)

            if tree is None:
                continue

            for node in ast.walk(tree):

                if isinstance(node, ast.ClassDef):

                    results.append({
                        "name": node.name,
                        "file": str(file_path),
                        "line": node.lineno
                    })

        return results

    def find_functions(self):
        """Find every function and async function."""

        results = []

        for file_path in self.get_source_files():

            tree = self._parse_file(file_path)

            if tree is None:
                continue

            for node in ast.walk(tree):

                if isinstance(
                    node,
                    (ast.FunctionDef, ast.AsyncFunctionDef)
                ):

                    results.append({
                        "name": node.name,
                        "file": str(file_path),
                        "line": node.lineno
                    })

        return results

    def find_methods(self):
        """Find methods defined inside classes."""

        results = []

        for file_path in self.get_source_files():

            tree = self._parse_file(file_path)

            if tree is None:
                continue

            for class_node in ast.walk(tree):

                if not isinstance(class_node, ast.ClassDef):
                    continue

                for node in class_node.body:

                    if isinstance(
                        node,
                        (ast.FunctionDef, ast.AsyncFunctionDef)
                    ):

                        results.append({
                            "class": class_node.name,
                            "method": node.name,
                            "file": str(file_path),
                            "line": node.lineno
                        })

        return results

    def find_imports(self):
        """Find all imports in the repository."""

        results = []

        for file_path in self.get_source_files():

            tree = self._parse_file(file_path)

            if tree is None:
                continue

            for node in ast.walk(tree):

                if isinstance(node, ast.Import):

                    for alias in node.names:

                        results.append({
                            "module": alias.name,
                            "file": str(file_path),
                            "line": node.lineno
                        })

                elif isinstance(node, ast.ImportFrom):

                    module = node.module or ""

                    results.append({
                        "module": module,
                        "file": str(file_path),
                        "line": node.lineno
                    })

        return results

    def find_function_calls(self, function_name):
        """
        Find calls to a particular function or method.

        Example:
            find_function_calls("connect")
        """

        if not function_name:
            return []

        results = []

        for file_path in self.get_source_files():

            tree = self._parse_file(file_path)

            if tree is None:
                continue

            for node in ast.walk(tree):

                if not isinstance(node, ast.Call):
                    continue

                called_name = self._get_call_name(node)

                if called_name == function_name:

                    results.append({
                        "function": function_name,
                        "file": str(file_path),
                        "line": node.lineno
                    })

        return results

    @staticmethod
    def _get_call_name(node):
        """Extract the name from an AST Call node."""

        if isinstance(node.func, ast.Name):
            return node.func.id

        if isinstance(node.func, ast.Attribute):
            return node.func.attr

        return None

    def find_class_methods(self, class_name):
        """Find all methods belonging to a specific class."""

        if not class_name:
            return []

        return [
            result
            for result in self.find_methods()
            if result["class"] == class_name
        ]
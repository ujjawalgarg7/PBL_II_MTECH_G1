from pathlib import Path
import ast

from src.repository.repo_ingestor import RepositoryIngestor
from src.code_understanding.code_parser import CodeParser
from src.code_search.ast_search import ASTSearch
from src.code_search.code_search import CodeSearch

from src.memory.short_term_memory import ShortTermMemory
from src.memory.episodic_memory import EpisodicMemory
from src.memory.semantic_memory import SemanticMemory

from src.memory.memory_retriever import MemoryRetriever


class RepositoryAgent:
    """
    Repository analysis agent.

    The agent can:

    - ingest arbitrary local repositories or folders
    - inspect repository structure
    - understand Python source code
    - search source code
    - perform AST searches
    - use short-term, episodic and semantic memory
    - retrieve relevant memories
    - perform basic static bug/issue detection

    Bug detection is heuristic. Findings represent potential
    problems that should be reviewed rather than guaranteed bugs.
    """

    def __init__(self, repository_path):

        self.repository_path = Path(
            repository_path
        ).resolve()

        # Repository components
        self.ingestor = RepositoryIngestor(
            self.repository_path
        )

        self.parser = CodeParser(
            self.repository_path
        )

        self.ast_search = ASTSearch(
            self.repository_path
        )

        self.code_search = CodeSearch(
            self.repository_path
        )

        # Memory components
        self.short_term_memory = ShortTermMemory()

        self.episodic_memory = EpisodicMemory()

        self.semantic_memory = SemanticMemory()

        # Retrieval component
        self.memory_retriever = MemoryRetriever(
            self.short_term_memory,
            self.episodic_memory,
            self.semantic_memory,
        )

    # ------------------------------------------------------------------
    # Repository inspection
    # ------------------------------------------------------------------

    def inspect_repository(self):
        """
        Inspect the repository and return a complete
        high-level analysis.
        """

        summary = self.ingestor.summary()

        structure = self.ingestor.get_structure()

        code_analysis = self.parser.analyze_repository()

        return {
            "summary": summary,
            "structure": structure,
            "code_analysis": code_analysis,
        }

    def repository_summary(self):
        """Return only the repository summary."""

        return self.ingestor.summary()

    # ------------------------------------------------------------------
    # Code search
    # ------------------------------------------------------------------

    def search_code(self, query):
        """Search text across the repository."""

        results = self.code_search.search_text(
            query
        )

        self.short_term_memory.add(
            f"Code search for '{query}' returned "
            f"{len(results)} results."
        )

        return results

    def search_symbol(self, symbol_name):
        """Search for a class or function."""

        results = self.code_search.search_symbol(
            symbol_name
        )

        self.short_term_memory.add(
            f"Symbol search for '{symbol_name}' returned "
            f"{len(results)} results."
        )

        return results

    # ------------------------------------------------------------------
    # AST search
    # ------------------------------------------------------------------

    def find_classes(self):
        """Find all classes."""

        return self.ast_search.find_classes()

    def find_functions(self):
        """Find all functions."""

        return self.ast_search.find_functions()

    def find_methods(self):
        """Find all methods."""

        return self.ast_search.find_methods()

    def find_imports(self):
        """Find all imports."""

        return self.ast_search.find_imports()

    def find_function_calls(self, function_name):
        """Find calls to a function."""

        return self.ast_search.find_function_calls(
            function_name
        )

    # ------------------------------------------------------------------
    # Static issue / bug analysis
    # ------------------------------------------------------------------

    def analyze_bugs(self):
        """
        Perform basic static analysis of Python files.

        Returns:
            list[dict]: Potential issues found in the repository.

        Findings are heuristic and should be reviewed by a developer.
        """

        findings = []

        for file_path in self.parser.get_source_files():

            try:
                source = file_path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )

                tree = ast.parse(source)

            except SyntaxError as error:

                findings.append({
                    "type": "syntax_error",
                    "severity": "high",
                    "file": str(file_path),
                    "line": getattr(
                        error,
                        "lineno",
                        None,
                    ),
                    "message": str(error),
                })

                continue

            except OSError as error:

                findings.append({
                    "type": "file_error",
                    "severity": "medium",
                    "file": str(file_path),
                    "line": None,
                    "message": str(error),
                })

                continue

            findings.extend(
                self._analyze_ast(
                    tree,
                    file_path,
                )
            )

            findings.extend(
                self._analyze_source_lines(
                    source,
                    file_path,
                )
            )

        self.short_term_memory.add(
            f"Static analysis found "
            f"{len(findings)} potential issue(s)."
        )

        return findings

    def _analyze_ast(self, tree, file_path):
        """Analyze one AST for potentially problematic patterns."""

        findings = []

        for node in ast.walk(tree):

            # ----------------------------------------------------------
            # Bare except
            # ----------------------------------------------------------

            if isinstance(node, ast.ExceptHandler):

                if node.type is None:

                    findings.append({
                        "type": "bare_except",
                        "severity": "medium",
                        "file": str(file_path),
                        "line": node.lineno,
                        "message": (
                            "Bare except catches all exceptions. "
                            "Consider catching a specific exception."
                        ),
                    })

            # ----------------------------------------------------------
            # eval()
            # ----------------------------------------------------------

            if isinstance(node, ast.Call):

                function_name = self._get_call_name(
                    node
                )

                if function_name == "eval":

                    findings.append({
                        "type": "eval_usage",
                        "severity": "high",
                        "file": str(file_path),
                        "line": node.lineno,
                        "message": (
                            "eval() executes dynamically supplied "
                            "Python expressions and can introduce "
                            "security risks."
                        ),
                    })

                # ------------------------------------------------------
                # exec()
                # ------------------------------------------------------

                if function_name == "exec":

                    findings.append({
                        "type": "exec_usage",
                        "severity": "high",
                        "file": str(file_path),
                        "line": node.lineno,
                        "message": (
                            "exec() executes dynamically supplied "
                            "Python code and can introduce "
                            "security risks."
                        ),
                    })

                # ------------------------------------------------------
                # subprocess(..., shell=True)
                # ------------------------------------------------------

                if self._is_subprocess_call(node):

                    if self._has_shell_true(node):

                        findings.append({
                            "type": "subprocess_shell_true",
                            "severity": "high",
                            "file": str(file_path),
                            "line": node.lineno,
                            "message": (
                                "subprocess call uses shell=True. "
                                "Review input handling for command "
                                "injection risks."
                            ),
                        })

            # ----------------------------------------------------------
            # Mutable default arguments
            # ----------------------------------------------------------

            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ):

                findings.extend(
                    self._check_mutable_defaults(
                        node,
                        file_path,
                    )
                )

            # ----------------------------------------------------------
            # assert statements
            # ----------------------------------------------------------

            if isinstance(node, ast.Assert):

                findings.append({
                    "type": "assert_in_application_code",
                    "severity": "low",
                    "file": str(file_path),
                    "line": node.lineno,
                    "message": (
                        "assert statements can be disabled with "
                        "Python optimization. Consider explicit "
                        "validation for application logic."
                    ),
                })

            # ----------------------------------------------------------
            # == None / != None
            # ----------------------------------------------------------

            if isinstance(node, ast.Compare):

                for operator in node.ops:

                    if isinstance(
                        operator,
                        (
                            ast.Eq,
                            ast.NotEq,
                        ),
                    ):

                        for comparator in node.comparators:

                            if (
                                isinstance(
                                    comparator,
                                    ast.Constant,
                                )
                                and comparator.value is None
                            ):

                                findings.append({
                                    "type": "none_comparison",
                                    "severity": "low",
                                    "file": str(file_path),
                                    "line": node.lineno,
                                    "message": (
                                        "Use 'is None' or "
                                        "'is not None' instead of "
                                        "'== None' or '!= None'."
                                    ),
                                })

            # ----------------------------------------------------------
            # Unreachable code
            # ----------------------------------------------------------

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

                findings.extend(
                    self._check_unreachable_statements(
                        node,
                        file_path,
                    )
                )

            if isinstance(node, ast.Module):

                findings.extend(
                    self._check_unreachable_statements(
                        node,
                        file_path,
                    )
                )

        return findings

    def _analyze_source_lines(self, source, file_path):
        """Check source text for TODO/FIXME markers."""

        findings = []

        for line_number, line in enumerate(
            source.splitlines(),
            start=1,
        ):

            upper_line = line.upper()

            if "TODO" in upper_line:

                findings.append({
                    "type": "todo",
                    "severity": "low",
                    "file": str(file_path),
                    "line": line_number,
                    "message": (
                        "TODO marker found. "
                        "Review whether unfinished work remains."
                    ),
                    "content": line.strip(),
                })

            elif "FIXME" in upper_line:

                findings.append({
                    "type": "fixme",
                    "severity": "medium",
                    "file": str(file_path),
                    "line": line_number,
                    "message": (
                        "FIXME marker found. "
                        "Review the referenced code."
                    ),
                    "content": line.strip(),
                })

        return findings

    def _check_mutable_defaults(
        self,
        function_node,
        file_path,
    ):
        """Find mutable default function arguments."""

        findings = []

        defaults = list(
            function_node.args.defaults
        )

        defaults.extend(
            default
            for default in function_node.args.kw_defaults
            if default is not None
        )

        for default in defaults:

            if isinstance(
                default,
                (
                    ast.List,
                    ast.Dict,
                    ast.Set,
                ),
            ):

                findings.append({
                    "type": "mutable_default_argument",
                    "severity": "medium",
                    "file": str(file_path),
                    "line": function_node.lineno,
                    "message": (
                        f"Function '{function_node.name}' "
                        "uses a mutable default argument. "
                        "Use None and initialize inside the function."
                    ),
                })

        return findings

    def _check_unreachable_statements(
        self,
        node,
        file_path,
    ):
        """Detect simple unreachable statements."""

        findings = []

        body = getattr(
            node,
            "body",
            [],
        )

        terminated = False

        for statement in body:

            if terminated:

                findings.append({
                    "type": "unreachable_code",
                    "severity": "medium",
                    "file": str(file_path),
                    "line": statement.lineno,
                    "message": (
                        "Statement appears after a return, raise, "
                        "break or continue and may be unreachable."
                    ),
                })

            if isinstance(
                statement,
                (
                    ast.Return,
                    ast.Raise,
                    ast.Break,
                    ast.Continue,
                ),
            ):

                terminated = True

        return findings

    @staticmethod
    def _get_call_name(node):
        """Return the function name used by an AST Call."""

        if not isinstance(node, ast.Call):
            return None

        if isinstance(node.func, ast.Name):
            return node.func.id

        if isinstance(node.func, ast.Attribute):
            return node.func.attr

        return None

    @staticmethod
    def _is_subprocess_call(node):
        """Check whether an AST call belongs to subprocess."""

        if not isinstance(node, ast.Call):
            return False

        if isinstance(node.func, ast.Attribute):

            if isinstance(
                node.func.value,
                ast.Name,
            ):

                return (
                    node.func.value.id == "subprocess"
                )

        return False

    @staticmethod
    def _has_shell_true(node):
        """Check whether shell=True is supplied."""

        for keyword in node.keywords:

            if keyword.arg != "shell":
                continue

            if (
                isinstance(
                    keyword.value,
                    ast.Constant,
                )
                and keyword.value.value is True
            ):
                return True

        return False

    # ------------------------------------------------------------------
    # Memory
    # ------------------------------------------------------------------

    def remember_event(
        self,
        event,
        reason=None,
        importance=0.5,
        task_id=None,
    ):
        """Store an important debugging event."""

        self.episodic_memory.add_event(
            event=event,
            reason=reason,
            importance=importance,
            task_id=task_id,
        )

    def remember_fact(
        self,
        key,
        value,
        importance=0.5,
        source=None,
        verified=False,
    ):
        """Store a stable repository fact."""

        self.semantic_memory.add_fact(
            key=key,
            value=value,
            importance=importance,
            source=source,
            verified=verified,
        )

    def retrieve_memory(
        self,
        query,
        task_id=None,
    ):
        """Retrieve ranked memories relevant to a query."""

        return self.memory_retriever.retrieve(
            query,
            task_id=task_id,
        )

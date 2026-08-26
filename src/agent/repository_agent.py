from src.repository.repo_ingestor import RepositoryIngestor
from src.code_understanding.code_parser import CodeParser
from src.code_search.ast_search import ASTSearch
from src.code_search.code_search import CodeSearch

from src.memory.short_term_memory import ShortTermMemory
from src.memory.episodic_memory import EpisodicMemory
from src.memory.semantic_memory import SemanticMemory

from src.retrieval.retrieval import MemoryRetriever


class RepositoryAgent:
    """
    Integrates repository ingestion, code understanding,
    code search and the memory system.

    The agent can inspect an arbitrary local repository,
    understand its Python source structure, store useful
    information in memory and retrieve relevant information.
    """

    def __init__(self, repository_path):

        self.repository_path = repository_path

        # Repository components
        self.ingestor = RepositoryIngestor(
            repository_path
        )

        self.parser = CodeParser(
            repository_path
        )

        self.ast_search = ASTSearch(
            repository_path
        )

        self.code_search = CodeSearch(
            repository_path
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

    def repository_summary(self):
        """Return only the repository summary."""

        return self.ingestor.summary()
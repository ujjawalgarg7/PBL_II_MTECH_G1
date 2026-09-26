import json
from pathlib import Path

from src.llm.rag_bug_analyzer import RAGBugAnalyzer
from src.memory.short_term_memory import ShortTermMemory
from src.memory.episodic_memory import EpisodicMemory
from src.memory.semantic_memory import SemanticMemory
from src.memory.memory_retriever import MemoryRetriever


class RepositoryBugDetector:
    """
    End-to-end repository bug detection pipeline.

    Flow:

        Repository
            ↓
        Python source files
            ↓
        RAGBugAnalyzer
            ↓
        BugsInPy retrieval
            ↓
        Memory retrieval
            ↓
        Ollama LLM
            ↓
        Bug report

    This class is responsible for integrating the existing
    repository, RAG, LLM, and memory components.
    """

    def __init__(
        self,
        dataset_path="data/bugsinpy_llm_sample.json",
        model=None,
        memory_capacity=100,
    ):
        self.dataset_path = dataset_path

        # Existing RAG + Ollama analyzer.
        self.analyzer = RAGBugAnalyzer(
            dataset_path=dataset_path,
            model=model,
        )

        # Existing memory layers.
        self.short_term_memory = ShortTermMemory(
            capacity=memory_capacity
        )

        self.episodic_memory = EpisodicMemory(
            capacity=memory_capacity
        )

        self.semantic_memory = SemanticMemory()

        # Existing memory retrieval system.
        self.memory_retriever = MemoryRetriever(
            short_term_memory=self.short_term_memory,
            episodic_memory=self.episodic_memory,
            semantic_memory=self.semantic_memory,
        )

    def _find_python_files(self, repository_path):
        """
        Find Python files inside a repository.

        Common generated/cache directories are ignored.
        """

        repository_path = Path(repository_path)

        if not repository_path.exists():
            raise FileNotFoundError(
                f"Repository not found: {repository_path}"
            )

        if repository_path.is_file():
            if repository_path.suffix.lower() == ".py":
                return [repository_path]

            raise ValueError(
                "The supplied file is not a Python file."
            )

        ignored_directories = {
            ".git",
            ".venv",
            "venv",
            "env",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            "site-packages",
            "dist",
            "build",
        }

        python_files = []

        for path in repository_path.rglob("*.py"):
            if any(
                part in ignored_directories
                for part in path.parts
            ):
                continue

            python_files.append(path)

        return sorted(python_files)

    def _read_file(self, path):
        """
        Read a Python source file safely.
        """

        try:
            return path.read_text(
                encoding="utf-8"
            )

        except UnicodeDecodeError:
            return path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

    def _memory_query(self, source_code, file_path):
        """
        Create a query for previous memories.

        The query intentionally contains useful source
        information rather than the entire repository.
        """

        preview = source_code[:4000]

        return (
            f"Python bug analysis for file {file_path}\n"
            f"{preview}"
        )

    def _retrieve_memory(
        self,
        source_code,
        file_path,
        top_k=5,
        task_id=None,
    ):
        """
        Retrieve relevant memories from the existing
        memory system.
        """

        query = self._memory_query(
            source_code,
            file_path,
        )

        results = self.memory_retriever.retrieve(
            query,
            task_id=task_id,
        )

        return results[:top_k]

    def _store_analysis_memory(
        self,
        file_path,
        analysis,
        retrieved_examples,
        task_id=None,
    ):
        """
        Store the result of the analysis in episodic
        memory so later analyses can reuse it.
        """

        bugs = analysis.get(
            "bugs",
            [],
        )

        bug_count = len(bugs)

        event = (
            f"Analyzed Python file {file_path}. "
            f"Detected {bug_count} bug(s)."
        )

        if bugs:
            bug_types = [
                str(
                    bug.get(
                        "type",
                        "unknown",
                    )
                )
                for bug in bugs
            ]

            event += (
                " Bug types: "
                + ", ".join(bug_types)
                + "."
            )

        reason = (
            "Repository bug detection result "
            "stored for future analysis."
        )

        importance = 0.8 if bug_count else 0.5

        self.episodic_memory.add_event(
            event=event,
            reason=reason,
            importance=importance,
            task_id=task_id,
        )

    def analyze_file(
        self,
        file_path,
        top_k=3,
        memory_top_k=5,
        task_id=None,
    ):
        """
        Analyze one Python file.

        Returns:
            Dictionary containing:
                - file
                - analysis
                - retrieved BugsInPy examples
                - retrieved memories
        """

        path = Path(file_path)

        source_code = self._read_file(
            path
        )

        memories = self._retrieve_memory(
            source_code,
            str(path),
            top_k=memory_top_k,
            task_id=task_id,
        )

        result = self.analyzer.analyze(
            source_code,
            top_k=top_k,
            memories=memories,
        )

        analysis = result.get(
            "analysis",
            {},
        )

        self._store_analysis_memory(
            file_path=str(path),
            analysis=analysis,
            retrieved_examples=result.get(
                "retrieved_examples",
                [],
            ),
            task_id=task_id,
        )

        return {
            "file": str(path),
            "analysis": analysis,
            "retrieved_examples": result.get(
                "retrieved_examples",
                [],
            ),
            "retrieved_memories": memories,
            "llm_used": result.get(
                "llm_used",
                False,
            ),
        }

    def analyze_repository(
        self,
        repository_path,
        top_k=3,
        memory_top_k=5,
        task_id=None,
    ):
        """
        Analyze all Python files in a repository.

        This is the main entry point for the system.
        """

        repository_path = Path(
            repository_path
        )

        python_files = self._find_python_files(
            repository_path
        )

        results = []

        total_bugs = 0

        for file_path in python_files:
            try:
                result = self.analyze_file(
                    file_path=file_path,
                    top_k=top_k,
                    memory_top_k=memory_top_k,
                    task_id=task_id,
                )

                analysis = result.get(
                    "analysis",
                    {},
                )

                bugs = analysis.get(
                    "bugs",
                    [],
                )

                total_bugs += len(bugs)

                results.append(
                    result
                )

            except Exception as exc:
                results.append(
                    {
                        "file": str(file_path),
                        "analysis": {
                            "bug_found": False,
                            "bugs": [],
                        },
                        "error": str(exc),
                        "llm_used": False,
                    }
                )

        return {
            "repository": str(
                repository_path
            ),
            "files_scanned": len(
                python_files
            ),
            "files_with_bugs": sum(
                1
                for result in results
                if result.get(
                    "analysis",
                    {},
                ).get(
                    "bug_found",
                    False,
                )
            ),
            "total_bugs": total_bugs,
            "results": results,
        }

    def save_report(
        self,
        report,
        output_path="reports/bug_report.json",
    ):
        """
        Save the complete repository bug report.
        """

        output_path = Path(
            output_path
        )

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            json.dumps(
                report,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return output_path

    def get_memory_summary(self):
        """
        Return a summary of the current memory state.
        """

        return {
            "short_term": len(
                self.short_term_memory
            ),
            "episodic": len(
                self.episodic_memory
            ),
            "semantic": len(
                self.semantic_memory
            ),
        }

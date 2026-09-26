# Module guide

## `src.agent`

**Purpose:** repository exploration API.

**Key class:** `RepositoryAgent`.

**Input/output:** takes a local repository path. `inspect_repository()` returns a repository summary, directory structure, and parsed code analysis. Search methods return lists of file/line/symbol records; `analyze_bugs()` returns heuristic findings.

**Connections:** composes `RepositoryIngestor`, `CodeParser`, `CodeSearch`, `ASTSearch`, the three memory stores, and `MemoryRetriever`. This is an exploration track; it is not called by the CLI RAG demo.

## `src.memory`

**Purpose:** retain and rank context across exploration and analysis.

**Key classes:** `ShortTermMemory`, `EpisodicMemory`, `SemanticMemory`, and `MemoryRetriever`.

**Input/output:** short-term memory stores recent items; episodic memory stores event dictionaries with timestamp, importance, reason, and optional task ID; semantic memory stores keyed facts. All stores return copies of their current content and support JSON `save(path)` / `load(path)`. `MemoryRetriever.retrieve(query, task_id=None)` returns scored memory records.

**Connections:** used by both `RepositoryAgent` and `RepositoryBugDetector`. The demo persists the stores in `.memory/`. `src.retrieval.retrieval` is a backward-compatible re-export of the canonical retriever in this package.

## `src.llm`

**Purpose:** analyze Python code using deterministic checks, BugsInPy retrieval, and an optional local LLM request.

**Key classes/modules:** `OllamaClient`, `BugContextRetriever`, `RAGBugAnalyzer`, `RepositoryBugDetector`, and the `demo` CLI. `BugAnalyzer` and `LLMBugAnalyzer` are additional standalone analyzer implementations.

**Input/output:** `RepositoryBugDetector.analyze_repository(path)` returns a dictionary containing repository totals and per-file analysis, retrieved example metadata, retrieved memories, and errors where applicable. `RAGBugAnalyzer` takes source text and returns merged findings.

**Connections:** `RAGBugAnalyzer` queries `BugContextRetriever` over processed JSON examples, builds an Ollama prompt containing source/static findings/examples/memory, and merges the response with trusted static findings. The demo loads and saves memory around detector execution.

## `src.dataset`

**Purpose:** turn BugsInPy metadata and project revisions into RAG-ready examples.

**Key classes:** `BugsInPyLoader`, `BugSourceExtractor`, `BugDatasetBuilder`, and `BugDatasetPreprocessor`.

**Input/output:** given a BugsInPy root, the loader yields `BugExample` metadata; the extractor returns changed Python files with `buggy_code` and `fixed_code`; the builder writes raw JSON; the preprocessor writes LLM-ready JSON with `input.buggy_source` and `target.patch`.

**Connections:** the preprocessor’s output is read by `src.llm.bug_context.BugContextRetriever`. The source extractor uses Git and may clone project repositories.

## `src.repository`

**Purpose:** inventory a local repository.

**Key classes:** `RepositoryIngestor`, `RepositoryManifest`, and `FileRecord`.

**Input/output:** both take a repository path. The ingestor returns file records, a structure list, and extension-based summary; the manifest returns classified file records and aggregate statistics.

**Connections:** `RepositoryAgent` uses `RepositoryIngestor`; `RepositoryManifest` is a standalone structured inventory suitable for later consumers.

## `src.code_search`

**Purpose:** find text and Python syntax structures across a local repository.

**Key classes:** `CodeSearch` and `ASTSearch`.

**Input/output:** `CodeSearch` returns file/line/content matches, symbol records, or matching filenames. `ASTSearch` returns classes, functions, methods, imports, call sites, or class methods as lists of dictionaries.

**Connections:** `RepositoryAgent` exposes these methods as its search interface. Searches focus on `.py` files; their directory-ignore behavior differs slightly by class, so callers should treat results as inspection aids rather than a complete language-agnostic index.

## `src.code_understanding`

**Purpose:** parse Python files and extract basic structural information.

**Key class:** `CodeParser`.

**Input/output:** accepts a Python file or directory. `analyze_repository()` returns one record per Python file with classes, functions, methods, and imports, or a syntax-error record.

**Connections:** `RepositoryAgent.inspect_repository()` includes this analysis. The parser relies on Python’s built-in `ast` module and does not build cross-file semantic relationships.

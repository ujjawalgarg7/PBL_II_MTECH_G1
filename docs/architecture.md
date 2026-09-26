# Architecture

## Component diagram

```text
                         Local repository / GitHub URL
                                      |
                                      v
                         src.llm.demo (CLI lifecycle)
                                      |
                 +--------------------+--------------------+
                 |                                         |
                 v                                         v
    RepositoryAgent explorer                    RepositoryBugDetector
    ------------------------                    ---------------------
    RepositoryIngestor                          Python file discovery
    CodeParser                                  RAGBugAnalyzer
    CodeSearch / ASTSearch                      MemoryRetriever
    heuristic static checks                     Short/Episodic/Semantic memory
                 |                                         |
                 v                                         v
      structures, symbols, searches             static AST checks + BugsInPy retrieval
                                                          |
                                                          v
                                OllamaClient -> qwen2.5-coder:3b
                                                          |
                                                          v
                                     merged localized bug report
                                                          |
                                                          v
                                     console report + .memory/*.json
```

`RepositoryAgent` and `RepositoryBugDetector` are parallel Phase 1 entry points. The former is an exploration API. The latter is the demo’s end-to-end bug-analysis path. They share the same memory-store classes and canonical `MemoryRetriever` implementation.

## Analysis data flow

```text
Repository input
  -> demo resolves local path or shallow-clones a GitHub URL
  -> detector finds Python files
  -> source is read for one file
  -> MemoryRetriever ranks relevant short-term, episodic, semantic entries
  -> RAGBugAnalyzer runs deterministic AST checks
  -> BugContextRetriever lexically retrieves BugsInPy examples
  -> source + static findings + examples + memories are sent to Ollama
  -> JSON response is parsed; LLM locations are checked where possible
  -> static and LLM findings are merged
  -> report prints file, line, and source snippet
  -> episodic result is stored; demo saves all memories as JSON
```

The Explorer flow is separate:

```text
RepositoryAgent
  -> RepositoryIngestor / RepositoryManifest for file metadata
  -> CodeParser for classes, functions, methods, imports
  -> CodeSearch and ASTSearch for targeted inspection
  -> heuristic issue findings and memory updates
```

## Dataset pipeline

```text
BugsInPy checkout
  -> BugsInPyLoader reads bug.info, patch, and optional scripts
  -> BugSourceExtractor obtains project Git repository
  -> compare buggy_commit_id with fixed_commit_id
  -> git show reads changed Python files at both commits
  -> BugDatasetBuilder writes raw examples with buggy_code/fixed_code
  -> BugDatasetPreprocessor combines buggy_code into input.buggy_source
  -> LLM-ready JSON consumed by BugContextRetriever
```

The RAG retriever uses lexical token overlap, not an embedding index or vector database.

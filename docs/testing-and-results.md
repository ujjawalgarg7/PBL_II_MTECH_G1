# Testing and results

## Run the suite

From the project root, install `pytest` and run:

```powershell
python -m pip install pytest
python -m pytest
```

Useful focused commands:

```powershell
python -m pytest tests\agent tests\repository tests\code_search tests\code_understanding -q
python -m pytest tests\memory -q
python -m pytest tests\llm tests\dataset -q
```

## Coverage

The requested Phase 1 baseline describes 73 tests. The current checkout contains **77 named test functions**, because it also includes added regression coverage for prompt-memory integration, JSON persistence, dataset source-field handling, demo persistence, and localization. The count should be treated as a repository snapshot, not a performance metric.

The tests cover:

- **Explorer and repository utilities:** repository ingestion, manifest construction, AST parsing, text/symbol searches, AST structural searches, and `RepositoryAgent` behavior.
- **Memory:** capacity behavior, retrieval/ranking across short-term, episodic, and semantic stores, JSON save/load, and location-rich episodic analysis records.
- **Prompt integration:** retrieved memory is forwarded from `RepositoryBugDetector` to `RAGBugAnalyzer` and appears in the prompt context.
- **Persistence:** the demo writes memory after an analysis and restores it for a later run.
- **Dataset and localization:** preprocessing consumes `buggy_code`; LLM line locations are rejected or corrected in targeted cases; reports print source snippets.

## What is not unit-tested

The suite does **not** make a live Ollama request or assert model quality. It does not benchmark BugsInPy retrieval quality, clone external repositories, execute a analyzed repository’s tests, or verify generated fixes—because Phase 1 does not generate/apply patches and has no verifier.

Consequently, passing tests demonstrates behavior of the local deterministic code and mocked integration boundaries; it does not establish that an LLM finding is correct for a real repository.

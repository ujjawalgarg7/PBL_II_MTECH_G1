# PBL II MTech G1 — Phase 1 Python Bug Detection

This repository is a Phase 1 foundation for exploring Python repositories and identifying potential bugs. It is designed around a future multi-agent workflow: today it provides a repository-exploration agent and an LLM-assisted bug-detection pipeline, but it does not yet orchestrate multiple agents.

## Problem statement

Reviewing an unfamiliar Python repository requires structural understanding, targeted search, historical context, and careful bug localization. This project combines deterministic inspection with local retrieval-augmented generation (RAG) to produce developer-reviewable reports. It does not claim that every reported issue is a confirmed defect.

## Phase 1 scope

- Explore local Python repositories through file inventory, AST parsing, text/symbol search, and AST search.
- Maintain short-term, episodic, and semantic memory; rank relevant memory for later work.
- Persist demo memory between runs as JSON under `.memory/`.
- Analyze Python files using deterministic checks plus BugsInPy retrieval and Ollama.
- Print localized reports containing file, line, and source-line context.
- Build LLM-ready JSON examples from BugsInPy buggy/fixed revisions.

Patch generation, target-test execution, fix verification, embedding retrieval, and multi-agent orchestration are outside Phase 1.

## Architecture overview

The repository has two tracks.

1. **RepositoryAgent explorer** — `src.agent.repository_agent.RepositoryAgent` brings together repository ingestion, AST parsing, text and symbol search, structural AST search, basic static issue checks, and three memory types.
2. **RAG bug analyzer** — `src.llm.repository_bug_detector.RepositoryBugDetector` runs `RAGBugAnalyzer`, which combines Python AST checks, lexical BugsInPy retrieval, relevant persisted memories, and Ollama. The default local model is `qwen2.5-coder:3b`.

See [the architecture guide](docs/architecture.md) for flows and component relationships.

## Setup

Python 3.10 or later is required. The application code uses the standard library; install `pytest` for the test suite.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pytest
```

Install Ollama and fetch the configured model:

```powershell
ollama pull qwen2.5-coder:3b
```

The RAG path expects `data/bugsinpy_llm_sample.json`, which is included in this checkout. For rebuilding examples from BugsInPy, follow [dataset instructions](docs/dataset.md).

## Quick demo

Start Ollama, then run the demo from the repository root with either a local repository path or a GitHub URL:

```powershell
python -m src.llm.demo C:\path\to\python-repository
python -m src.llm.demo https://github.com/owner/repository
```

The demo creates `.memory/` in the current working directory, loads prior JSON memory if available, prints the report, and saves memory after successful analysis.

Run the tests with:

```powershell
python -m pytest
```

## Documentation

- [Phase 1 report](docs/phase-1-report.md)
- [Architecture](docs/architecture.md)
- [Setup and usage](docs/setup-and-usage.md)
- [Module guide](docs/modules.md)
- [Dataset pipeline](docs/dataset.md)
- [Testing and results](docs/testing-and-results.md)

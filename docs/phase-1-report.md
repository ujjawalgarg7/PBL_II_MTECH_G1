# Phase 1 Report

## Objective

Phase 1 establishes a practical foundation for Python repository exploration and bug detection. The repository contains two complementary tracks: a `RepositoryAgent` for deterministic inspection and search, and an LLM-assisted `RepositoryBugDetector` that combines static checks, BugsInPy retrieval, persistent memory, and a local Ollama model.

The goal is to return reviewable bug reports, not to prove correctness or automatically repair code.

## What is implemented

### Repository exploration

`RepositoryAgent` composes repository ingestion, Python AST parsing, text/symbol search, AST search, basic static issue checks, and memory retrieval. It can summarize a repository, list its structure, find symbols and calls, and record search activity in short-term memory.

### AST parsing and static bug checks

`CodeParser`, `ASTSearch`, and `CodeSearch` provide structural and text-level inspection. `RAGBugAnalyzer` performs deterministic AST checks for syntax errors, mutable defaults, `eval`, `exec`, `os.system`, bare `except`, `assert` used for runtime validation, and literal division/modulo by zero. Static findings remain available even when the LLM call fails.

### RAG bug analysis

`RAGBugAnalyzer` retrieves lexically relevant BugsInPy examples, combines them with static findings and source code, then prompts a local Ollama model. The default client model is `qwen2.5-coder:3b`. LLM findings are merged with static findings, with basic line-number validation and de-duplication.

### Memory retrieval in the LLM prompt

`RepositoryBugDetector` retrieves ranked short-term, episodic, and semantic memories before each file analysis. Those results are passed into `RAGBugAnalyzer` and rendered as a `Relevant Past Memories` prompt section. Past memories are explicitly supporting evidence, not ground truth.

### Memory persistence across demo runs

The three memory stores expose JSON `save()` and `load()` methods. `src.llm.demo` loads `.memory/short_term.json`, `.memory/episodic.json`, and `.memory/semantic.json` when present, then saves them after a successful analysis. Episodic entries record bug file and line locations.

### Dataset pipeline

The BugsInPy loader reads bug metadata and patches. The source extractor clones project repositories when needed, compares buggy and fixed commits, and reads changed Python files at both revisions. The preprocessor converts extracted examples into the JSON structure consumed by the RAG retriever.

## Methods

1. Accept a local repository path or clone a GitHub repository in the demo.
2. Enumerate Python files while excluding common generated and environment directories.
3. Read each file, retrieve related memory, run deterministic AST checks, and retrieve BugsInPy examples using lexical overlap.
4. Send source, static findings, historical examples, and relevant memory to Ollama.
5. Parse the requested JSON response, validate LLM locations where possible, merge it with static findings, and print a report with a source-line snippet.
6. Persist memory state for the next demo run.

## Representative demo output

The exact findings depend on the repository, dataset matches, and Ollama response. The following is the output shape emitted by `python -m src.llm.demo <repository>`; values are illustrative rather than a claimed benchmark result.

```text
========================================
       REPOSITORY BUG ANALYSIS
========================================

Repository: C:\path\to\repository
Files scanned: 4
Files with bugs: 1
Total bugs: 1

----------------------------------------
BUG #1
----------------------------------------
File: C:\path\to\repository\example.py
Line: 12
Code: result = eval(user_input)
Type: security_risk
Severity: HIGH

Message:
eval() executes dynamically supplied Python code and may allow code injection.

Suggestion:
Avoid eval() and use a safe alternative.

----------------------------------------
Memory
----------------------------------------
Previous relevant analysis retrieved: 0

LLM: Ollama
Dataset: BugsInPy
Memory: Enabled
========================================
```

## Limitations and next steps

These are Phase 2 concerns, not completed Phase 1 capabilities:

- LLM findings can still include false positives despite prompt constraints, static evidence, and basic line validation.
- The system reports suggested fixes but does not generate or apply patches.
- The code has components called agents, but it does not yet implement multi-agent orchestration, delegation, or coordination.
- The analysis pipeline does not execute a target repository's tests or use a verifier to confirm findings or fixes.
- Retrieval is simple lexical matching rather than embedding/vector retrieval, and the dataset-building path needs network access, Git, and compatible historical commits.

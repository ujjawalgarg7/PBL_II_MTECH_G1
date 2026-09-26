# Setup and usage

## Prerequisites

- Python 3.10+ (the project uses modern union type syntax).
- Git, for cloning GitHub inputs and rebuilding BugsInPy examples.
- Ollama, for the RAG demo’s LLM call.
- `pytest`, for tests.

There is currently no `requirements.txt` or third-party runtime package requirement in the repository. Install the test runner explicitly:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install pytest
```

On macOS/Linux, activate with `source .venv/bin/activate`.

## Ollama

Install Ollama using its platform installer, start its local service if it is not already running, and pull the default model used by `OllamaClient`:

```powershell
ollama pull qwen2.5-coder:3b
ollama list
```

The client sends requests to `http://localhost:11434/api/generate` with a 120-second timeout. A connection failure is reported as an Ollama runtime error; deterministic static findings are still available inside `RAGBugAnalyzer` when the LLM call fails.

## BugsInPy setup

The repository includes a small processed dataset at `data/bugsinpy_llm_sample.json`, so the demo does not require a full BugsInPy rebuild. To use the source dataset pipeline, clone BugsInPy at the repository root:

```powershell
git clone https://github.com/soarsmu/BugsInPy.git BugsInPy
```

On PowerShell, expose its framework commands for the current shell if you need upstream BugsInPy commands:

```powershell
$env:Path += ";$PWD\BugsInPy\framework\bin"
```

The extractor itself invokes Git directly and expects a BugsInPy directory with `projects/<project>/...` metadata. It clones benchmark project repositories into a sibling `bug_repositories/` directory when required.

## Run the demo

From the project root, after Ollama is available:

```powershell
python -m src.llm.demo C:\path\to\python-repository
python -m src.llm.demo https://github.com/owner/repository
```

Omit the argument for interactive input:

```powershell
python -m src.llm.demo
```

The demo accepts only a local directory or a GitHub HTTP(S) URL. It creates `.memory/` in the current working directory and restores/saves the three JSON memory snapshots around a successful analysis.

## Run tests

```powershell
python -m pytest
python -m pytest tests\memory -q
python -m pytest tests\llm -q
```

The unit suite does not require Ollama. Tests that exercise prompt assembly, persistence, and localization use local test doubles or direct method calls rather than a live model.

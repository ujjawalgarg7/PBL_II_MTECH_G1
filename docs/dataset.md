# BugsInPy dataset pipeline

## Source

[BugsInPy](https://github.com/soarsmu/BugsInPy) is the upstream benchmark used for historical bug examples. This repository expects a local BugsInPy checkout with a `projects/` directory. A processed sample used by the default RAG analyzer is included at `data/bugsinpy_llm_sample.json`.

## Extracting source at buggy and fixed commits

`src.dataset.bugsinpy_loader.BugsInPyLoader` reads each bug directory’s `bug.info`, `bug_patch.txt`, and optional requirements/setup/test paths. It exposes a `BugExample` containing project name, bug ID, Python version, buggy/fixed commit IDs, test-file metadata, and patch text.

`src.dataset.bug_source_extractor.BugSourceExtractor` then:

1. Reads the project Git URL from `projects/<project>/project.info`.
2. Clones the project into `<parent-of-BugsInPy>/bug_repositories/<project>` if it is not already present.
3. Ensures both buggy and fixed commits are available, fetching Git refs if necessary.
4. Runs `git diff --name-only <buggy> <fixed>` to identify changed files.
5. Keeps changed Python files and uses `git show <commit>:<file>` to read each file at both revisions.
6. Produces file records with `file`, `buggy_code`, and `fixed_code`.

`BugDatasetBuilder` combines that source data with loader metadata and writes raw examples. It is a programmatic API, for example:

```python
from src.dataset.bug_dataset_builder import BugDatasetBuilder

builder = BugDatasetBuilder("BugsInPy")
builder.save_json("data/bugsinpy_raw.json", limit=5)
```

This operation requires network access and Git if project repositories or commits are absent.

## Preprocessing to LLM examples

`BugDatasetPreprocessor` reads raw builder JSON. For every file entry it uses `buggy_code` (not the fixed revision), prefixes it with a `===== FILE: ... =====` header, and joins all changed Python files into `input.buggy_source`. It keeps the source benchmark’s patch and test-file metadata as the target.

```python
from src.dataset.bug_dataset_preprocessor import BugDatasetPreprocessor

preprocessor = BugDatasetPreprocessor("data/bugsinpy_raw.json")
preprocessor.save_json("data/bugsinpy_llm.json")
```

## LLM-ready schema

Each processed example has this shape:

```json
{
  "project": "example-project",
  "bug_id": "1",
  "input": {
    "buggy_source": "===== FILE: package/module.py =====\n...",
    "test_file": "tests/test_module.py"
  },
  "target": {
    "patch": "diff --git ...",
    "fixed_commit_id": "optional-fixed-commit-id"
  }
}
```

`BugContextRetriever` loads a JSON list in this format and scores examples through lexical token overlap with source code and static findings. It supplies retrieved buggy source, test-file information, and patches to the RAG prompt as historical context only.

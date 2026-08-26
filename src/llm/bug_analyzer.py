"""
LLM Bug Analyzer

Provides deterministic AST-based bug detection and an optional LLM layer.
"""

from pathlib import Path
import ast
import json
from typing import Any, Callable, Dict, List, Optional


class BugAnalyzer:
    """Analyze Python source code for potential bugs."""

    def __init__(self, model: Optional[Callable[[str], Any]] = None):
        self.model = model

    def build_prompt(self, source_code: str, file_name: str = "unknown.py") -> str:
        """Build the prompt sent to the LLM."""
        return f"""Analyze the following Python file for bugs.

File:
{file_name}

Source code:
```python
{source_code}
```

Return JSON in this format:
{{
  "bugs": [
    {{
      "type": "bug type",
      "severity": "low|medium|high|critical",
      "line": 1,
      "message": "explanation",
      "suggestion": "how to fix it"
    }}
  ]
}}

Only report bugs with a reasonable technical basis.
"""

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Python file not found: {file_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        source = path.read_text(encoding="utf-8")
        return self.analyze_code(source, str(path))

    def analyze_code(self, source_code: str, file_name: str = "unknown.py") -> Dict[str, Any]:
        static_bugs = self._static_analysis(source_code)
        llm_result = {"bugs": []}

        if self.model is not None:
            try:
                response = self.model(self.build_prompt(source_code, file_name))
                llm_result = self._parse_llm_response(response)
            except Exception as exc:
                llm_result = {"bugs": [{
                    "type": "llm_error",
                    "severity": "low",
                    "line": None,
                    "message": str(exc),
                    "suggestion": "Check the configured LLM provider."
                }]}

        bugs = self._remove_duplicates(
            static_bugs + llm_result.get("bugs", [])
        )

        return {
            "file": file_name,
            "bug_count": len(bugs),
            "bugs": bugs,
            "llm_used": self.model is not None,
        }

    def analyze_repository(self, repository_path: str) -> Dict[str, Any]:
        root = Path(repository_path)
        if not root.exists():
            raise FileNotFoundError(f"Repository not found: {repository_path}")

        reports = []
        total = 0
        ignored = {".git", "__pycache__", ".venv", "venv", "env", "node_modules"}

        for path in root.rglob("*.py"):
            if any(part in ignored for part in path.parts):
                continue

            try:
                report = self.analyze_file(str(path))
            except (SyntaxError, UnicodeDecodeError) as exc:
                report = {
                    "file": str(path),
                    "bug_count": 1,
                    "bugs": [{
                        "type": "parse_error",
                        "severity": "high",
                        "line": getattr(exc, "lineno", None),
                        "message": str(exc),
                        "suggestion": "Fix the syntax or encoding error."
                    }],
                    "llm_used": False,
                }

            reports.append(report)
            total += report["bug_count"]

        return {
            "repository": str(root),
            "files_analyzed": len(reports),
            "bug_count": total,
            "files": reports,
        }

    def analyze_json(self, source_code: str, file_name: str = "unknown.py") -> str:
        return json.dumps(
            self.analyze_code(source_code, file_name),
            indent=2,
            ensure_ascii=False,
        )

    def _static_analysis(self, source_code: str) -> List[Dict[str, Any]]:
        try:
            tree = ast.parse(source_code)
        except SyntaxError as exc:
            return [{
                "type": "syntax_error",
                "severity": "high",
                "line": exc.lineno,
                "message": exc.msg,
                "suggestion": "Fix the syntax error before executing the file.",
            }]

        bugs = []
        bugs.extend(self._check_mutable_defaults(tree))
        bugs.extend(self._check_eval(tree))
        bugs.extend(self._check_unreachable(tree))
        bugs.extend(self._check_bare_except(tree))
        bugs.extend(self._check_assert(tree))
        return bugs

    def _check_mutable_defaults(self, tree: ast.AST) -> List[Dict[str, Any]]:
        bugs = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            defaults = list(node.args.defaults)
            defaults.extend(x for x in node.args.kw_defaults if x is not None)

            if any(isinstance(x, (ast.List, ast.Dict, ast.Set)) for x in defaults):
                bugs.append({
                    "type": "mutable_default_argument",
                    "severity": "medium",
                    "line": node.lineno,
                    "message": f"Function '{node.name}' uses a mutable default argument.",
                    "suggestion": "Use None as the default and initialize the value inside the function.",
                })
        return bugs

    def _check_eval(self, tree: ast.AST) -> List[Dict[str, Any]]:
        bugs = []
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "eval"):
                bugs.append({
                    "type": "eval_usage",
                    "severity": "high",
                    "line": node.lineno,
                    "message": "eval() executes dynamically supplied Python expressions and can introduce security risks.",
                    "suggestion": "Avoid eval(); use a safe parser or explicit allowed operations.",
                })
        return bugs

    def _check_unreachable(self, tree: ast.AST) -> List[Dict[str, Any]]:
        bugs = []
        for node in ast.walk(tree):
            body = getattr(node, "body", None)
            if not isinstance(body, list):
                continue

            terminated = False
            for statement in body:
                if terminated:
                    bugs.append({
                        "type": "unreachable_code",
                        "severity": "medium",
                        "line": statement.lineno,
                        "message": "Statement appears after return, raise, break or continue and may be unreachable.",
                        "suggestion": "Remove the unreachable statement or restructure the control flow.",
                    })
                    continue

                if isinstance(statement, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                    terminated = True
        return bugs

    def _check_bare_except(self, tree: ast.AST) -> List[Dict[str, Any]]:
        bugs = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                bugs.append({
                    "type": "bare_except",
                    "severity": "medium",
                    "line": node.lineno,
                    "message": "Bare except catches all exceptions.",
                    "suggestion": "Catch specific exception types.",
                })
        return bugs

    def _check_assert(self, tree: ast.AST) -> List[Dict[str, Any]]:
        bugs = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                bugs.append({
                    "type": "assert_for_runtime_validation",
                    "severity": "low",
                    "line": node.lineno,
                    "message": "assert statements can be disabled with Python optimization.",
                    "suggestion": "Use an explicit exception for required runtime validation.",
                })
        return bugs

    def _parse_llm_response(self, response: Any) -> Dict[str, Any]:
        if isinstance(response, dict):
            return response

        if hasattr(response, "content"):
            response = response.content

        if not isinstance(response, str):
            return {"bugs": []}

        text = response.strip()

        if text.startswith("```"):
            lines = text.splitlines()[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            result = json.loads(text)
            return result if isinstance(result, dict) else {"bugs": []}
        except json.JSONDecodeError:
            return {
                "bugs": [{
                    "type": "llm_analysis",
                    "severity": "unknown",
                    "line": None,
                    "message": text,
                    "suggestion": "",
                }]
            }

    def _remove_duplicates(self, bugs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        unique = []
        seen = set()

        for bug in bugs:
            key = (
                bug.get("type"),
                bug.get("line"),
                bug.get("message"),
            )
            if key not in seen:
                seen.add(key)
                unique.append(bug)

        return unique


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze Python code for bugs.")
    parser.add_argument("path", help="Python file or repository path")
    args = parser.parse_args()

    analyzer = BugAnalyzer()
    target = Path(args.path)

    if target.is_file():
        result = analyzer.analyze_file(str(target))
    else:
        result = analyzer.analyze_repository(str(target))

    print(json.dumps(result, indent=2, ensure_ascii=False))
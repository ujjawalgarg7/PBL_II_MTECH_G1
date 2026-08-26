import ast
import json
from pathlib import Path

from src.llm.ollama_client import OllamaClient


class LLMBugAnalyzer:
    """LLM-powered Python bug analyzer."""

    def __init__(self, model="qwen2.5-coder:3b"):
        self.client = OllamaClient(model=model)

    def read_file(self, file_path):
        return Path(file_path).read_text(encoding="utf-8")

    def get_ast_context(self, source):
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            return {
                "syntax_error": str(exc),
                "functions": [],
                "classes": [],
                "imports": [],
            }

        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)

        return {
            "syntax_error": None,
            "functions": functions,
            "classes": classes,
            "imports": imports,
        }

    def build_prompt(self, source, file_path,
                     static_findings=None, retrieved_context=None):
        static_findings = static_findings or []
        retrieved_context = retrieved_context or []
        ast_context = self.get_ast_context(source)

        return f"""
You are a Python software debugging assistant.

Analyze the Python source below.

Rules:
1. Do NOT report SyntaxError unless the source is genuinely invalid Python.
2. Do NOT invent bugs.
3. Only report bugs supported by evidence in the source.
4. Distinguish bugs from style suggestions.
5. If uncertain, use low confidence.
6. Return ONLY valid JSON.
7. The JSON must contain a "bugs" array.

Each bug must contain:
type, severity, line, message, suggestion, confidence

Severity: low, medium, high, critical
Confidence: low, medium, high

File:
{file_path}

AST context:
{json.dumps(ast_context, indent=2)}

Existing static-analysis findings:
{json.dumps(static_findings, indent=2)}

Relevant retrieved bug knowledge:
{json.dumps(retrieved_context, indent=2)}

Python source:
```python
{source}
```

Return ONLY JSON.
"""

    def analyze(self, file_path, static_findings=None,
                retrieved_context=None):
        source = self.read_file(file_path)

        prompt = self.build_prompt(
            source,
            str(file_path),
            static_findings,
            retrieved_context,
        )

        response = self.client.generate(prompt)
        result = self._parse_response(response)
        result["file"] = str(file_path)
        result["llm_used"] = True
        return result

    def _parse_response(self, response):
        response = response.strip()

        if response.startswith("```"):
            lines = response.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response = "\n".join(lines).strip()

        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            return {
                "bugs": [],
                "raw_response": response,
                "parse_error": True,
            }

        if not isinstance(result, dict):
            return {
                "bugs": [],
                "raw_response": response,
                "parse_error": True,
            }

        bugs = result.get("bugs", [])
        if not isinstance(bugs, list):
            bugs = []

        normalized = []

        for bug in bugs:
            if not isinstance(bug, dict):
                continue

            normalized.append({
                "type": bug.get("type", "unknown"),
                "severity": bug.get("severity", "medium"),
                "line": bug.get("line"),
                "message": bug.get("message", ""),
                "suggestion": bug.get("suggestion", ""),
                "confidence": bug.get("confidence", "low"),
            })

        return {
            "bugs": normalized,
            "parse_error": False,
        }


def main():
    import sys

    if len(sys.argv) != 2:
        print(
            "Usage: python -m src.llm.llm_bug_analyzer "
            "<python_file>"
        )
        return

    analyzer = LLMBugAnalyzer()
    result = analyzer.analyze(sys.argv[1])

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
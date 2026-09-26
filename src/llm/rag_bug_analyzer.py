import ast
import json
import re
from pathlib import Path

from src.llm.ollama_client import OllamaClient
from src.llm.bug_context import BugContextRetriever


class RAGBugAnalyzer:
    """
    Reliable Python bug analyzer.

    Pipeline:

        Source Code
             |
             +---- Static Analysis
             |
             +---- BugsInPy Retrieval
             |
             +---- Ollama LLM
             |
             +---- Combined Findings

    Static analysis is used for obvious Python bugs so that
    results do not randomly disappear when the LLM produces
    a different answer.
    """

    def __init__(
        self,
        dataset_path="data/bugsinpy_llm_sample.json",
        model=None,
    ):
        self.retriever = BugContextRetriever(dataset_path)

        if model:
            self.llm = OllamaClient(model=model)
        else:
            self.llm = OllamaClient()

    # =========================================================
    # STATIC ANALYSIS
    # =========================================================

    def _static_analysis(self, source_code):
        """
        Detect common Python bugs using the Python AST.

        These findings are deterministic and do not depend
        on the LLM response.
        """

        bugs = []

        try:
            tree = ast.parse(source_code)

        except SyntaxError as error:
            return [
                {
                    "type": "syntax_error",
                    "severity": "high",
                    "line": error.lineno or 1,
                    "message": (
                        f"Python syntax error: {error.msg}."
                    ),
                    "suggestion": (
                        "Fix the syntax error before running "
                        "the program."
                    ),
                }
            ]

        # -----------------------------------------------------
        # Mutable default arguments
        # -----------------------------------------------------

        for node in ast.walk(tree):

            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

                defaults = list(node.args.defaults)

                defaults += [
                    default
                    for default in node.args.kw_defaults
                    if default is not None
                ]

                for default in defaults:

                    if isinstance(
                        default,
                        (ast.List, ast.Dict, ast.Set),
                    ):
                        bugs.append(
                            {
                                "type": "mutable_default_argument",
                                "severity": "medium",
                                "line": node.lineno,
                                "message": (
                                    f"Function '{node.name}' uses "
                                    "a mutable default argument."
                                ),
                                "suggestion": (
                                    "Use None as the default value "
                                    "and create the list, dictionary, "
                                    "or set inside the function."
                                ),
                            }
                        )

        # -----------------------------------------------------
        # eval()
        # -----------------------------------------------------

        for node in ast.walk(tree):

            if isinstance(node, ast.Call):

                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id == "eval"
                ):
                    bugs.append(
                        {
                            "type": "security_risk",
                            "severity": "high",
                            "line": node.lineno,
                            "message": (
                                "eval() executes dynamically supplied "
                                "Python code and may allow code injection."
                            ),
                            "suggestion": (
                                "Avoid eval() and use a safe alternative."
                            ),
                        }
                    )

        # -----------------------------------------------------
        # exec()
        # -----------------------------------------------------

        for node in ast.walk(tree):

            if isinstance(node, ast.Call):

                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id == "exec"
                ):
                    bugs.append(
                        {
                            "type": "security_risk",
                            "severity": "high",
                            "line": node.lineno,
                            "message": (
                                "exec() executes dynamically supplied "
                                "Python code and can create security risks."
                            ),
                            "suggestion": (
                                "Avoid exec() and use explicit program "
                                "logic instead."
                            ),
                        }
                    )

        # -----------------------------------------------------
        # os.system()
        # -----------------------------------------------------

        for node in ast.walk(tree):

            if isinstance(node, ast.Call):

                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "system"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "os"
                ):
                    bugs.append(
                        {
                            "type": "security_risk",
                            "severity": "high",
                            "line": node.lineno,
                            "message": (
                                "os.system() executes a shell command "
                                "and may be unsafe with untrusted input."
                            ),
                            "suggestion": (
                                "Use subprocess with an argument list "
                                "and validate untrusted input."
                            ),
                        }
                    )

        # -----------------------------------------------------
        # Bare except
        # -----------------------------------------------------

        for node in ast.walk(tree):

            if isinstance(node, ast.ExceptHandler):

                if node.type is None:
                    bugs.append(
                        {
                            "type": "bare_except",
                            "severity": "medium",
                            "line": node.lineno,
                            "message": (
                                "A bare except catches every exception, "
                                "including exceptions that should normally "
                                "not be swallowed."
                            ),
                            "suggestion": (
                                "Catch the specific exceptions that the "
                                "program is expected to handle."
                            ),
                        }
                    )

        # -----------------------------------------------------
        # Dangerous assert usage
        # -----------------------------------------------------

        for node in ast.walk(tree):

            if isinstance(node, ast.Assert):

                bugs.append(
                    {
                        "type": "assert_for_validation",
                        "severity": "low",
                        "line": node.lineno,
                        "message": (
                            "assert statements can be disabled with "
                            "Python optimization and should not be used "
                            "for critical runtime validation."
                        ),
                        "suggestion": (
                            "Use an explicit condition and raise an "
                            "appropriate exception for runtime validation."
                        ),
                    }
                )

        # -----------------------------------------------------
        # Possible division by zero
        # -----------------------------------------------------

        for node in ast.walk(tree):

            if isinstance(node, ast.BinOp):

                if isinstance(
                    node.op,
                    (
                        ast.Div,
                        ast.FloorDiv,
                        ast.Mod,
                    ),
                ):

                    if isinstance(node.right, ast.Constant):

                        if node.right.value == 0:

                            bugs.append(
                                {
                                    "type": "division_by_zero",
                                    "severity": "high",
                                    "line": node.lineno,
                                    "message": (
                                        "The expression performs "
                                        "division or modulo by zero."
                                    ),
                                    "suggestion": (
                                        "Check that the divisor is not "
                                        "zero before performing the operation."
                                    ),
                                }
                            )

        return bugs

    # =========================================================
    # PROMPT
    # =========================================================

    def _build_prompt(
        self,
        source_code,
        retrieved_examples,
        static_findings,
        memories=None,
    ):
        """Build the Ollama prompt."""

        context_parts = []

        for example in retrieved_examples:

            input_data = example.get(
                "input",
                {},
            )

            target_data = example.get(
                "target",
                {},
            )

            context_parts.append(
                f"""
Historical BugsInPy Example

Project:
{example.get("project")}

Bug ID:
{example.get("bug_id")}

Buggy Source:
{input_data.get("buggy_source", "")}

Test File:
{input_data.get("test_file", "")}

Known Patch:
{target_data.get("patch", "")}
"""
            )

        historical_context = "\n".join(context_parts)

        static_context = json.dumps(
            static_findings,
            indent=2,
            ensure_ascii=False,
        )

        memory_context = json.dumps(
            memories or [],
            indent=2,
            ensure_ascii=False,
            default=str,
        )

        return f"""
You are a Python software bug detection assistant.

Analyze the following Python source code carefully.

SOURCE CODE:
----------------
{source_code}
----------------

Deterministic static-analysis findings:
----------------
{static_context}
----------------

Historical BugsInPy examples that may contain
similar bugs:

{historical_context}

Relevant Past Memories:
----------------
{memory_context}
----------------

Use BugsInPy examples only as supporting evidence.

Use past memories only as supporting evidence. Verify that
they apply to the current source code.

Do not assume that a historical bug exists in the
current source code.

The static-analysis findings are also supporting
evidence. Verify them against the source code.

Look for additional bugs that static analysis may
have missed.

Return ONLY valid JSON.

Required format:

{{
  "bug_found": true,
  "bugs": [
    {{
      "type": "bug type",
      "severity": "low|medium|high|critical",
      "line": 1,
      "message": "clear explanation",
      "suggestion": "how to fix it"
    }}
  ]
}}

If there are no bugs:

{{
  "bug_found": false,
  "bugs": []
}}

Rules:

1. Return JSON only.
2. Do not use Markdown.
3. Do not include ```json.
4. Do not invent bugs without evidence.
5. Use the actual source-code line number.
6. Report obvious security and correctness issues.
"""

    # =========================================================
    # RESPONSE PARSER
    # =========================================================

    def _parse_response(self, response):
        """Parse JSON returned by Ollama."""

        if isinstance(response, dict):
            return response

        if response is None:
            return {
                "bug_found": False,
                "bugs": [],
                "parse_error": "Empty LLM response.",
            }

        text = str(response).strip()

        # Remove Markdown code fences.
        if text.startswith("```"):

            lines = text.splitlines()

            if lines:
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines).strip()

        # Try direct JSON.
        try:
            return json.loads(text)

        except json.JSONDecodeError:
            pass

        # Try extracting JSON object from surrounding text.
        start = text.find("{")
        end = text.rfind("}")

        if start >= 0 and end > start:

            candidate = text[start:end + 1]

            try:
                return json.loads(candidate)

            except json.JSONDecodeError:
                pass

        return {
            "bug_found": False,
            "bugs": [],
            "raw_response": response,
            "parse_error": (
                "LLM did not return valid JSON."
            ),
        }

    # =========================================================
    # MERGE FINDINGS
    # =========================================================

    @staticmethod
    def _llm_line_anchor(bug):
        """Return a source-code marker for bug types with clear syntax."""

        description = " ".join(
            [
                str(bug.get("type", "")).lower(),
                str(bug.get("message", "")).lower(),
            ]
        )

        anchors = (
            ("eval", r"\beval\s*\("),
            ("exec", r"\bexec\s*\("),
            ("division_by_zero", r"//|/|%"),
            ("mutable_default", r"\bdef\b"),
            ("hardcoded", r"password|secret|token|api[_-]?key"),
            ("sql_injection", r"execute|executemany|query"),
        )

        for keyword, pattern in anchors:
            if keyword in description:
                return pattern

        return None

    def _validate_llm_bug_line(self, bug, source_code):
        """Return an LLM bug with a trustworthy location, or ``None``."""

        line = bug.get("line")

        if isinstance(line, bool):
            return None

        try:
            line = int(line)
        except (TypeError, ValueError):
            return None

        source_lines = source_code.splitlines()

        if not 1 <= line <= len(source_lines):
            return None

        # Normalize numeric strings returned by the LLM before merging.
        bug = dict(bug)
        bug["line"] = line

        candidate = source_lines[line - 1].strip()
        anchor = self._llm_line_anchor(bug)

        # A blank/comment location cannot describe an executable bug. When a
        # bug type has a recognizable code marker, relocate it to that marker.
        clearly_unrelated = not candidate or candidate.startswith("#")

        if anchor and not re.search(anchor, candidate, re.IGNORECASE):
            clearly_unrelated = True

        if clearly_unrelated:
            if not anchor:
                return None

            matching_lines = [
                index
                for index, text in enumerate(source_lines, start=1)
                if re.search(anchor, text, re.IGNORECASE)
            ]

            if not matching_lines:
                return None

            line = min(matching_lines, key=lambda value: abs(value - line))
            bug["line"] = line

        return bug

    def _merge_findings(
        self,
        static_findings,
        llm_analysis,
        source_code=None,
    ):
        """
        Combine static findings and LLM findings.

        Duplicate bugs are removed using type + line.
        Static findings are preserved because they are
        deterministic.
        """

        merged = []

        seen = set()

        # Static findings first.
        for bug in static_findings:

            bug_type = str(
                bug.get("type", "")
            ).lower()

            line = bug.get("line")

            key = (
                bug_type,
                line,
            )

            if key not in seen:

                seen.add(key)
                merged.append(bug)

        # LLM findings.
        if isinstance(llm_analysis, dict):

            llm_bugs = llm_analysis.get(
                "bugs",
                [],
            )

            if isinstance(llm_bugs, list):

                for bug in llm_bugs:

                    if not isinstance(bug, dict):
                        continue

                    if source_code is not None:
                        bug = self._validate_llm_bug_line(
                            bug,
                            source_code,
                        )

                        if bug is None:
                            continue

                    bug_type = str(
                        bug.get("type", "")
                    ).lower()

                    line = bug.get("line")

                    key = (
                        bug_type,
                        line,
                    )

                    # Also check same line with a related
                    # security/correctness finding.
                    duplicate = key in seen

                    if not duplicate:

                        seen.add(key)
                        merged.append(bug)

        return {
            "bug_found": bool(merged),
            "bugs": merged,
        }

    # =========================================================
    # MAIN ANALYSIS
    # =========================================================

    def analyze(
        self,
        source_code,
        top_k=3,
        memories=None,
    ):
        """
        Analyze Python source code using:

        1. Static analysis
        2. BugsInPy retrieval
        3. Ollama
        4. Combined findings
        """

        # -----------------------------------------------------
        # Static analysis
        # -----------------------------------------------------

        static_findings = self._static_analysis(
            source_code
        )

        # -----------------------------------------------------
        # Historical BugsInPy retrieval
        # -----------------------------------------------------

        retrieved = (
            self.retriever.retrieve_for_code(
                source_code,
                static_findings=static_findings,
                top_k=top_k,
            )
        )

        # -----------------------------------------------------
        # Ollama
        # -----------------------------------------------------

        prompt = self._build_prompt(
            source_code,
            retrieved,
            static_findings,
            memories,
        )

        try:

            response = self.llm.generate(
                prompt
            )

            llm_analysis = self._parse_response(
                response
            )

        except Exception as error:

            # If Ollama fails, static analysis can
            # still produce useful results.
            llm_analysis = {
                "bug_found": False,
                "bugs": [],
                "llm_error": str(error),
            }

        # -----------------------------------------------------
        # Merge
        # -----------------------------------------------------

        combined = self._merge_findings(
            static_findings,
            llm_analysis,
            source_code,
        )

        result = {
            "analysis": combined,
            "retrieved_examples": [
                {
                    "project": item.get(
                        "project"
                    ),
                    "bug_id": item.get(
                        "bug_id"
                    ),
                    "score": item.get(
                        "retrieval_score"
                    ),
                }
                for item in retrieved
            ],
            "llm_used": True,
            "static_analysis_used": True,
        }

        if "llm_error" in llm_analysis:
            result["llm_error"] = (
                llm_analysis["llm_error"]
            )

        return result

    # =========================================================
    # FILE ANALYSIS
    # =========================================================

    def analyze_file(
        self,
        file_path,
        top_k=3,
    ):
        """Analyze one Python file."""

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {file_path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Expected a file: {file_path}"
            )

        source_code = path.read_text(
            encoding="utf-8"
        )

        result = self.analyze(
            source_code,
            top_k=top_k,
        )

        result["file"] = str(path)

        return result

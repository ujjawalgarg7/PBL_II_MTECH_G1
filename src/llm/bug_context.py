import json
import re
from pathlib import Path


class BugContextRetriever:
    """
    Retrieve relevant historical BugsInPy examples.

    Dataset format:

    {
        "project": "...",
        "bug_id": "...",
        "input": {
            "buggy_source": "...",
            "test_file": "..."
        },
        "target": {
            "patch": "...",
            "fixed_commit_id": "..."
        }
    }
    """

    def __init__(
        self,
        dataset_path="data/bugsinpy_llm_sample.json",
    ):
        self.dataset_path = Path(dataset_path)
        self.examples = self._load_dataset()

    def _load_dataset(self):
        """Load the BugsInPy dataset."""

        if not self.dataset_path.exists():
            raise FileNotFoundError(
                f"BugsInPy dataset not found: "
                f"{self.dataset_path}"
            )

        with self.dataset_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        if not isinstance(data, list):
            raise ValueError(
                "BugsInPy dataset must contain a JSON list."
            )

        return data

    def _get_search_text(self, example):
        """
        Extract all useful searchable information from
        one BugsInPy example.
        """

        input_data = example.get("input", {})
        target_data = example.get("target", {})

        if not isinstance(input_data, dict):
            input_data = {}

        if not isinstance(target_data, dict):
            target_data = {}

        parts = [
            str(example.get("project", "")),
            str(example.get("bug_id", "")),
            str(input_data.get("buggy_source", "")),
            str(input_data.get("test_file", "")),
            str(target_data.get("patch", "")),
            str(target_data.get("fixed_commit_id", "")),
        ]

        return " ".join(parts).lower()

    def _tokenize(self, text):
        """
        Convert text into searchable tokens.
        """

        return set(
            token.lower()
            for token in re.findall(
                r"[a-zA-Z_][a-zA-Z0-9_]*",
                text,
            )
            if len(token) > 2
        )

    def _score(self, query, example):
        """
        Calculate a simple lexical relevance score.
        """

        query_tokens = self._tokenize(query)

        if not query_tokens:
            return 0

        search_text = self._get_search_text(
            example
        )

        search_tokens = self._tokenize(
            search_text
        )

        matches = query_tokens.intersection(
            search_tokens
        )

        return len(matches)

    def retrieve(
        self,
        query,
        top_k=3,
    ):
        """
        Retrieve the most relevant BugsInPy examples.
        """

        scored = []

        for example in self.examples:
            score = self._score(
                query,
                example,
            )

            if score > 0:
                scored.append(
                    (
                        score,
                        example,
                    )
                )

        scored.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        results = []

        for score, example in scored[:top_k]:
            result = {
                "project": example.get(
                    "project"
                ),
                "bug_id": example.get(
                    "bug_id"
                ),
                "input": example.get(
                    "input",
                    {},
                ),
                "target": example.get(
                    "target",
                    {},
                ),
                "retrieval_score": score,
            }

            results.append(result)

        return results

    def retrieve_for_code(
        self,
        source_code,
        static_findings=None,
        top_k=3,
    ):
        """
        Retrieve historical bugs relevant to source code.
        """

        query_parts = [
            source_code
        ]

        if static_findings:
            query_parts.append(
                json.dumps(
                    static_findings,
                    ensure_ascii=False,
                )
            )

        query = "\n".join(
            query_parts
        )

        return self.retrieve(
            query,
            top_k=top_k,
        )

    def format_for_llm(
        self,
        results,
    ):
        """
        Format retrieved BugsInPy examples as
        compact context for the LLM.
        """

        formatted = []

        for result in results:

            input_data = result.get(
                "input",
                {},
            )

            target_data = result.get(
                "target",
                {},
            )

            formatted.append(
                {
                    "project": result.get(
                        "project"
                    ),
                    "bug_id": result.get(
                        "bug_id"
                    ),
                    "buggy_source": input_data.get(
                        "buggy_source",
                        "",
                    ),
                    "test_file": input_data.get(
                        "test_file",
                        "",
                    ),
                    "patch": target_data.get(
                        "patch",
                        "",
                    ),
                    "retrieval_score": result.get(
                        "retrieval_score",
                        0,
                    ),
                }
            )

        return formatted
from pathlib import Path
import json


class BugDatasetPreprocessor:
    """Convert BugsInPy examples into LLM training examples."""

    def __init__(self, dataset_path):
        self.dataset_path = Path(dataset_path)

    def load_examples(self):
        """Load raw BugsInPy examples from JSON."""

        if not self.dataset_path.exists():
            raise FileNotFoundError(
                f"Dataset file does not exist: {self.dataset_path}"
            )

        return json.loads(
            self.dataset_path.read_text(
                encoding="utf-8"
            )
        )

    @staticmethod
    def _combine_files(files):
        """Combine repository files into one source string."""

        parts = []

        for file_data in files:
            file_name = file_data.get("file", "")
            source = file_data.get("buggy_code", "")

            parts.append(
                f"===== FILE: {file_name} =====\n"
                f"{source}"
            )

        return "\n\n".join(parts)

    def process_example(self, example):
        """Convert one raw example into an LLM example."""

        buggy_source = self._combine_files(
            example.get("files", [])
        )

        return {
            "project": example.get("project"),
            "bug_id": example.get("bug_id"),
            "input": {
                "buggy_source": buggy_source,
                "test_file": example.get("test_file"),
            },
            "target": {
                "patch": example.get("patch"),
                "fixed_commit_id": example.get(
                    "fixed_commit_id"
                ),
            },
        }

    def process_all(self):
        """Convert all examples."""

        examples = self.load_examples()

        return [
            self.process_example(example)
            for example in examples
        ]

    def save_json(self, output_path):
        """Save processed LLM examples."""

        processed = self.process_all()

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            json.dumps(
                processed,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return output_path

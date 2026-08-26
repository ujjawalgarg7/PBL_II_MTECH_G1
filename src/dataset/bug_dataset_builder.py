from pathlib import Path
import json

from src.dataset.bugsinpy_loader import BugsInPyLoader
from src.dataset.bug_source_extractor import BugSourceExtractor


class BugDatasetBuilder:
    """Build normalized LLM-ready examples from BugsInPy."""

    def __init__(self, dataset_path):
        self.loader = BugsInPyLoader(dataset_path)
        self.source_extractor = BugSourceExtractor(dataset_path)

    def build_example(self, project_name, bug_id):
        """Build one complete dataset example."""

        bug = self.loader.get_bug(
            project_name,
            bug_id,
        )

        if bug is None:
            return None

        source_data = self.source_extractor.extract_bug_source(
            project_name,
            bug_id,
        )

        return {
            "project": bug.project,
            "bug_id": bug.bug_id,
            "python_version": bug.python_version,
            "buggy_commit_id": bug.buggy_commit_id,
            "fixed_commit_id": bug.fixed_commit_id,
            "test_file": bug.test_file,
            "patch": bug.patch,
            "requirements_path": bug.requirements_path,
            "run_test_path": bug.run_test_path,
            "setup_path": bug.setup_path,
            "files": source_data["files"],
        }

    def build_examples(self, limit=None):
        """Build multiple complete dataset examples."""

        bugs = self.loader.load_examples()

        if limit is not None:
            bugs = bugs[:limit]

        examples = []

        for bug in bugs:
            example = self.build_example(
                bug.project,
                bug.bug_id,
            )

            if example is not None:
                examples.append(example)

        return examples

    def save_json(
        self,
        output_path,
        limit=None,
    ):
        """Build examples and save them as JSON."""

        examples = self.build_examples(
            limit=limit
        )

        output_path = Path(output_path)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            json.dumps(
                examples,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return output_path
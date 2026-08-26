from dataclasses import dataclass
from pathlib import Path


@dataclass
class BugExample:
    """Standard representation of one BugsInPy bug."""

    bug_id: str
    project: str
    python_version: str | None
    buggy_commit_id: str | None
    fixed_commit_id: str | None
    test_file: str | None
    patch: str
    requirements_path: str | None = None
    run_test_path: str | None = None
    setup_path: str | None = None

    def to_dict(self):
        """Convert the bug example into a dictionary."""

        return {
            "bug_id": self.bug_id,
            "project": self.project,
            "python_version": self.python_version,
            "buggy_commit_id": self.buggy_commit_id,
            "fixed_commit_id": self.fixed_commit_id,
            "test_file": self.test_file,
            "patch": self.patch,
            "requirements_path": self.requirements_path,
            "run_test_path": self.run_test_path,
            "setup_path": self.setup_path,
        }


class BugsInPyLoader:
    """
    Load bugs from the BugsInPy repository.

    Expected structure:

        BugsInPy/
            projects/
                project_name/
                    bugs/
                        bug_id/
                            bug.info
                            bug_patch.txt
                            requirements.txt
                            run_test.sh
                            setup.sh
    """

    def __init__(self, dataset_path):
        self.dataset_path = Path(dataset_path).resolve()

        if not self.dataset_path.exists():
            raise FileNotFoundError(
                f"BugsInPy dataset does not exist: "
                f"{self.dataset_path}"
            )

        if not self.dataset_path.is_dir():
            raise NotADirectoryError(
                f"BugsInPy dataset path is not a directory: "
                f"{self.dataset_path}"
            )

        self.projects_path = self.dataset_path / "projects"

        if not self.projects_path.is_dir():
            raise FileNotFoundError(
                f"BugsInPy projects directory not found: "
                f"{self.projects_path}"
            )

    def get_projects(self):
        """Return all BugsInPy project directories."""

        return sorted(
            path
            for path in self.projects_path.iterdir()
            if path.is_dir()
        )

    def get_bug_directories(self):
        """Return all bug directories across all projects."""

        results = []

        for project_path in self.get_projects():

            bugs_path = project_path / "bugs"

            if not bugs_path.is_dir():
                continue

            for bug_path in bugs_path.iterdir():

                if bug_path.is_dir():
                    results.append(bug_path)

        return sorted(results)

    def get_project_bugs(self, project_name):
        """Return bug directories for one project."""

        project_path = self.projects_path / project_name
        bugs_path = project_path / "bugs"

        if not project_path.is_dir():
            return []

        if not bugs_path.is_dir():
            return []

        return sorted(
            path
            for path in bugs_path.iterdir()
            if path.is_dir()
        )

    def read_bug_info(self, bug_path):
        """Read bug.info metadata."""

        bug_path = Path(bug_path)
        info_path = bug_path / "bug.info"

        if not info_path.exists():
            return {}

        metadata = {}

        for line in info_path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).splitlines():

            line = line.strip()

            if not line or "=" not in line:
                continue

            key, value = line.split(
                "=",
                1,
            )

            key = key.strip()
            value = value.strip()

            if (
                len(value) >= 2
                and value[0] == '"'
                and value[-1] == '"'
            ):
                value = value[1:-1]

            metadata[key] = value

        return metadata

    def read_patch(self, bug_path):
        """Read the ground-truth bug patch."""

        patch_path = Path(bug_path) / "bug_patch.txt"

        if not patch_path.exists():
            return ""

        return patch_path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

    def create_example(self, bug_path):
        """Convert one BugsInPy bug directory into BugExample."""

        bug_path = Path(bug_path)

        project_path = bug_path.parent.parent
        project_name = project_path.name

        metadata = self.read_bug_info(bug_path)

        patch = self.read_patch(bug_path)

        if not patch:
            return None

        return BugExample(
            bug_id=bug_path.name,
            project=project_name,
            python_version=metadata.get(
                "python_version"
            ),
            buggy_commit_id=metadata.get(
                "buggy_commit_id"
            ),
            fixed_commit_id=metadata.get(
                "fixed_commit_id"
            ),
            test_file=metadata.get(
                "test_file"
            ),
            patch=patch,
            requirements_path=self._optional_file(
                bug_path,
                "requirements.txt",
            ),
            run_test_path=self._optional_file(
                bug_path,
                "run_test.sh",
            ),
            setup_path=self._optional_file(
                bug_path,
                "setup.sh",
            ),
        )

    @staticmethod
    def _optional_file(
        bug_path,
        filename,
    ):
        """Return a file path if the file exists."""

        path = Path(bug_path) / filename

        if path.exists():
            return str(path)

        return None

    def load_examples(self):
        """Load all BugsInPy bug examples."""

        examples = []

        for bug_path in self.get_bug_directories():

            try:
                example = self.create_example(
                    bug_path
                )

            except OSError:
                continue

            if example is not None:
                examples.append(example)

        return examples

    def get_bug(
        self,
        project_name,
        bug_id,
    ):
        """Load one specific BugsInPy bug."""

        bugs = self.get_project_bugs(
            project_name
        )

        for bug_path in bugs:

            if bug_path.name == str(bug_id):
                return self.create_example(
                    bug_path
                )

        return None

    def inspect(self):
        """Return a high-level dataset summary."""

        projects = self.get_projects()
        bugs = self.get_bug_directories()

        return {
            "dataset_path": str(
                self.dataset_path
            ),
            "project_count": len(projects),
            "projects": [
                project.name
                for project in projects
            ],
            "bug_count": len(bugs),
        }
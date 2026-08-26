from pathlib import Path
import subprocess

from src.dataset.bugsinpy_loader import BugsInPyLoader


class BugSourceExtractor:
    """Extract buggy and fixed source code from BugsInPy commits."""

    def __init__(self, dataset_path):
        self.dataset_path = Path(dataset_path).resolve()
        self.loader = BugsInPyLoader(dataset_path)

        # Keep downloaded repositories outside BugsInPy itself.
        self.repositories_path = (
            self.dataset_path.parent / "bug_repositories"
        )

        self.repositories_path.mkdir(
            parents=True,
            exist_ok=True,
        )

    def _run_git(self, repository_path, *args):
        """Run a git command inside a repository."""

        result = subprocess.run(
            ["git", *args],
            cwd=repository_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
                or "Git command failed."
            )

        return result.stdout

    def get_github_url(self, project_name):
        """Read the GitHub URL from project.info."""

        project_path = (
            self.dataset_path
            / "projects"
            / project_name
        )

        info_path = project_path / "project.info"

        if not info_path.exists():
            raise FileNotFoundError(
                f"project.info not found: {info_path}"
            )

        for line in info_path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).splitlines():

            line = line.strip()

            if line.startswith("github_url="):

                value = line.split(
                    "=",
                    1,
                )[1].strip()

                if (
                    len(value) >= 2
                    and value[0] == '"'
                    and value[-1] == '"'
                ):
                    value = value[1:-1]

                return value

        raise ValueError(
            f"github_url not found in {info_path}"
        )

    def get_repository_path(self, project_name):
        """
        Return a local Git repository for a BugsInPy project.

        Clone it only if it has not already been downloaded.
        """

        repository_path = (
            self.repositories_path / project_name
        )

        if (repository_path / ".git").exists():
            return repository_path

        github_url = self.get_github_url(
            project_name
        )

        print(
            f"Cloning {project_name} from {github_url}..."
        )

        result = subprocess.run(
            [
                "git",
                "clone",
                github_url,
                str(repository_path),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
                or f"Unable to clone {github_url}"
            )

        return repository_path

    def get_changed_files(
        self,
        project_name,
        buggy_commit,
        fixed_commit,
    ):
        """Return files changed between two commits."""

        repository_path = self.get_repository_path(
            project_name
        )

        self._ensure_commit(
            repository_path,
            buggy_commit,
        )

        self._ensure_commit(
            repository_path,
            fixed_commit,
        )

        output = self._run_git(
            repository_path,
            "diff",
            "--name-only",
            buggy_commit,
            fixed_commit,
        )

        return [
            line.strip()
            for line in output.splitlines()
            if line.strip()
        ]

    def _ensure_commit(
        self,
        repository_path,
        commit,
    ):
        """Ensure a particular commit exists locally."""

        result = subprocess.run(
            [
                "git",
                "cat-file",
                "-e",
                f"{commit}^{{commit}}",
            ],
            cwd=repository_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )

        if result.returncode == 0:
            return

        print(
            f"Fetching commit {commit[:12]}..."
        )

        result = subprocess.run(
            [
                "git",
                "fetch",
                "--all",
                "--tags",
            ],
            cwd=repository_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
                or f"Unable to fetch commit {commit}"
            )

        result = subprocess.run(
            [
                "git",
                "cat-file",
                "-e",
                f"{commit}^{{commit}}",
            ],
            cwd=repository_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"Commit not found after fetching: {commit}"
            )

    def get_file_at_commit(
        self,
        project_name,
        commit,
        file_path,
    ):
        """Read a file from a specific commit."""

        repository_path = self.get_repository_path(
            project_name
        )

        self._ensure_commit(
            repository_path,
            commit,
        )

        try:
            return self._run_git(
                repository_path,
                "show",
                f"{commit}:{file_path}",
            )

        except RuntimeError:
            return None

    def extract_bug_source(
        self,
        project_name,
        bug_id,
    ):
        """Extract buggy and fixed source for one bug."""

        bug = self.loader.get_bug(
            project_name,
            bug_id,
        )

        if bug is None:
            return None

        if not bug.buggy_commit_id:
            return None

        if not bug.fixed_commit_id:
            return None

        changed_files = self.get_changed_files(
            project_name,
            bug.buggy_commit_id,
            bug.fixed_commit_id,
        )

        files = []

        for file_path in changed_files:

            if not file_path.endswith(".py"):
                continue

            buggy_code = self.get_file_at_commit(
                project_name,
                bug.buggy_commit_id,
                file_path,
            )

            fixed_code = self.get_file_at_commit(
                project_name,
                bug.fixed_commit_id,
                file_path,
            )

            files.append({
                "file": file_path,
                "buggy_code": buggy_code,
                "fixed_code": fixed_code,
            })

        return {
            "project": bug.project,
            "bug_id": bug.bug_id,
            "python_version": bug.python_version,
            "buggy_commit_id": bug.buggy_commit_id,
            "fixed_commit_id": bug.fixed_commit_id,
            "test_file": bug.test_file,
            "files": files,
            "patch": bug.patch,
        }
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from src.llm.repository_bug_detector import RepositoryBugDetector


def _memory_paths(memory_directory=Path(".memory")):
    """Return the JSON paths used to persist detector memory."""

    memory_directory = Path(memory_directory)

    return {
        "short_term_memory": memory_directory / "short_term.json",
        "episodic_memory": memory_directory / "episodic.json",
        "semantic_memory": memory_directory / "semantic.json",
    }


def _load_detector_memories(detector, memory_directory=Path(".memory")):
    """Load persisted memory when it exists; first runs start empty."""

    memory_directory = Path(memory_directory)
    memory_directory.mkdir(parents=True, exist_ok=True)

    for attribute, path in _memory_paths(memory_directory).items():
        if path.exists():
            getattr(detector, attribute).load(path)


def _save_detector_memories(detector, memory_directory=Path(".memory")):
    """Save all detector memory layers as JSON."""

    memory_directory = Path(memory_directory)
    memory_directory.mkdir(parents=True, exist_ok=True)

    for attribute, path in _memory_paths(memory_directory).items():
        getattr(detector, attribute).save(path)


def _source_line(file_path, line_number):
    """Return a stripped source line when the report location is readable."""

    try:
        line_number = int(line_number)

        if line_number <= 0:
            return None

        lines = Path(file_path).read_text(
            encoding="utf-8",
            errors="ignore",
        ).splitlines()

        if line_number > len(lines):
            return None

        return lines[line_number - 1].strip()

    except (OSError, TypeError, ValueError):
        return None


def print_report(report):
    print()
    print("=" * 40)
    print("       REPOSITORY BUG ANALYSIS")
    print("=" * 40)
    print()

    print(f"Repository: {report.get('repository')}")
    print(f"Files scanned: {report.get('files_scanned', 0)}")
    print(f"Files with bugs: {report.get('files_with_bugs', 0)}")
    print(f"Total bugs: {report.get('total_bugs', 0)}")
    print()

    bug_number = 0

    for result in report.get("results", []):
        analysis = result.get("analysis", {})
        bugs = analysis.get("bugs", [])

        if not bugs:
            continue

        for bug in bugs:
            bug_number += 1

            print("----------------------------------------")
            print(f"BUG #{bug_number}")
            print("----------------------------------------")

            print(f"File: {result.get('file')}")
            print(f"Line: {bug.get('line', 'N/A')}")

            source_line = _source_line(
                result.get("file"),
                bug.get("line"),
            )

            if source_line is not None:
                print(f"Code: {source_line}")

            print(f"Type: {bug.get('type', 'unknown')}")
            print(
                f"Severity: "
                f"{str(bug.get('severity', 'unknown')).upper()}"
            )
            print()

            print("Message:")
            print(bug.get("message", ""))
            print()

            print("Suggestion:")
            print(bug.get("suggestion", ""))
            print()

            retrieved = result.get(
                "retrieved_examples",
                []
            )

            if retrieved:
                print("----------------------------------------")
                print("Historical BugsInPy Context")
                print("----------------------------------------")

                for example in retrieved:
                    print(
                        f"{example.get('project')} "
                        f"#{example.get('bug_id')}"
                    )

                print()

    print("----------------------------------------")
    print("Memory")
    print("----------------------------------------")

    memory_count = 0

    for result in report.get("results", []):
        memory_count += len(
            result.get("retrieved_memories", [])
        )

    print(
        f"Previous relevant analysis retrieved: "
        f"{memory_count}"
    )
    print()

    print("LLM: Ollama")
    print("Dataset: BugsInPy")
    print("Memory: Enabled")

    print("=" * 40)


def is_github_url(value):
    """Return True if the input looks like a GitHub repository URL."""

    try:
        parsed = urlparse(value)

        return (
            parsed.scheme in ("http", "https")
            and parsed.netloc.lower() == "github.com"
        )

    except Exception:
        return False


def clone_repository(url):
    """
    Clone a GitHub repository into a temporary directory.

    Returns:
        Path to the cloned repository.
        Temporary directory is returned as well so the caller
        can clean it up afterwards.
    """

    parsed = urlparse(url)

    path_parts = [
        part
        for part in parsed.path.strip("/").split("/")
        if part
    ]

    if len(path_parts) < 2:
        raise ValueError(
            "Invalid GitHub repository URL. "
            "Expected something like "
            "https://github.com/user/repository"
        )

    repository_name = path_parts[-1]

    if repository_name.endswith(".git"):
        repository_name = repository_name[:-4]

    temp_directory = Path(
        tempfile.mkdtemp(
            prefix="repository_bug_analysis_"
        )
    )

    destination = temp_directory / repository_name

    print()
    print("GitHub repository detected.")
    print(f"Cloning: {url}")
    print("Please wait...")
    print()

    try:
        result = subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                url,
                str(destination),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    except FileNotFoundError:
        shutil.rmtree(
            temp_directory,
            ignore_errors=True,
        )

        raise RuntimeError(
            "Git was not found on PATH. "
            "Install Git and make sure 'git' works "
            "from PowerShell."
        )

    if result.returncode != 0:
        shutil.rmtree(
            temp_directory,
            ignore_errors=True,
        )

        error = result.stderr.strip()

        raise RuntimeError(
            "GitHub repository could not be cloned.\n"
            f"{error}"
        )

    return destination, temp_directory


def get_repository_input(command_line_value=None):
    """
    Get repository input either from the command line
    or interactively from the user.
    """

    if command_line_value:
        return command_line_value.strip()

    print()
    print("=" * 40)
    print("       REPOSITORY BUG ANALYZER")
    print("=" * 40)
    print()

    return input(
        "Enter GitHub URL or local repository path:\n> "
    ).strip()


def analyze_repository(repository_input):
    """
    Resolve a local repository or clone a GitHub repository,
    then run RepositoryBugDetector.
    """

    if not repository_input:
        raise ValueError(
            "Repository path or GitHub URL cannot be empty."
        )

    temporary_directory = None

    try:
        if is_github_url(repository_input):
            repository_path, temporary_directory = (
                clone_repository(repository_input)
            )
        else:
            repository_path = Path(
                repository_input
            ).expanduser().resolve()

            if not repository_path.exists():
                raise FileNotFoundError(
                    f"Repository does not exist: "
                    f"{repository_path}"
                )

            if not repository_path.is_dir():
                raise ValueError(
                    f"Expected a directory: "
                    f"{repository_path}"
                )

        print()
        print("Analyzing repository...")
        print("Please wait while Ollama analyzes the files.")
        print()

        detector = RepositoryBugDetector()

        _load_detector_memories(detector)

        report = detector.analyze_repository(
            str(repository_path)
        )

        _save_detector_memories(detector)

        # Show the original user input in the report.
        if is_github_url(repository_input):
            report["repository"] = repository_input

        return report

    finally:
        if temporary_directory is not None:
            print()
            print("Cleaning up temporary cloned repository...")

            shutil.rmtree(
                temporary_directory,
                ignore_errors=True,
            )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Analyze a local or GitHub Python repository "
            "using BugsInPy, Ollama and memory."
        )
    )

    parser.add_argument(
        "repository",
        nargs="?",
        help=(
            "Local repository path or GitHub repository URL. "
            "If omitted, interactive mode is used."
        ),
    )

    args = parser.parse_args()

    try:
        repository_input = get_repository_input(
            args.repository
        )

        report = analyze_repository(
            repository_input
        )

        print_report(report)

        return 0

    except KeyboardInterrupt:
        print("\nAnalysis cancelled.")
        return 1

    except Exception as exc:
        print()
        print("ERROR:")
        print(exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

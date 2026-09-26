from src.llm.demo import print_report
from src.llm.rag_bug_analyzer import RAGBugAnalyzer
from src.llm.repository_bug_detector import RepositoryBugDetector
from src.memory.episodic_memory import EpisodicMemory


def test_merge_relocates_llm_bug_to_relevant_source_line():
    analyzer = object.__new__(RAGBugAnalyzer)

    merged = analyzer._merge_findings(
        [],
        {
            "bugs": [
                {
                    "type": "eval_usage",
                    "line": 1,
                    "message": "Untrusted input reaches eval.",
                }
            ]
        },
        "value = 1\neval(user_input)",
    )

    assert merged["bugs"][0]["line"] == 2


def test_merge_rejects_missing_or_out_of_range_llm_lines():
    analyzer = object.__new__(RAGBugAnalyzer)

    merged = analyzer._merge_findings(
        [],
        {"bugs": [{"type": "unknown"}, {"type": "unknown", "line": 99}]},
        "value = 1",
    )

    assert merged["bugs"] == []


def test_report_prints_source_line_for_bug(tmp_path, capsys):
    source_file = tmp_path / "example.py"
    source_file.write_text("first = 1\n    dangerous = eval(value)   \n", encoding="utf-8")

    print_report(
        {
            "repository": str(tmp_path),
            "results": [
                {
                    "file": str(source_file),
                    "analysis": {"bugs": [{"line": 2, "type": "eval_usage"}]},
                }
            ],
        }
    )

    assert "Code: dangerous = eval(value)" in capsys.readouterr().out


def test_stored_memory_contains_bug_file_and_line():
    detector = object.__new__(RepositoryBugDetector)
    detector.episodic_memory = EpisodicMemory()

    detector._store_analysis_memory(
        file_path="src/example.py",
        analysis={"bugs": [{"type": "eval_usage", "line": 42}]},
        retrieved_examples=[],
    )

    event = detector.episodic_memory.get_all()[0]["event"]
    assert "src/example.py:42" in event

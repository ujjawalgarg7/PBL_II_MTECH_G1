from src.llm.rag_bug_analyzer import RAGBugAnalyzer
from src.llm.repository_bug_detector import RepositoryBugDetector


def test_prompt_includes_relevant_past_memories():
    analyzer = object.__new__(RAGBugAnalyzer)
    memories = [{"memory_type": "episodic", "content": {"event": "prior fix"}}]

    prompt = analyzer._build_prompt("x = 1", [], [], memories)

    assert "Relevant Past Memories:" in prompt
    assert "prior fix" in prompt


def test_repository_detector_forwards_memories_to_analyzer(tmp_path):
    source_file = tmp_path / "example.py"
    source_file.write_text("x = 1", encoding="utf-8")
    detector = object.__new__(RepositoryBugDetector)
    memories = [{"memory_type": "semantic", "content": {"key": "x"}}]

    class Analyzer:
        def __init__(self, expected_memories):
            self.expected_memories = expected_memories

        def analyze(self, source_code, top_k, memories):
            assert source_code == "x = 1"
            assert top_k == 3
            assert memories == self.expected_memories
            return {
                "analysis": {"bugs": []},
                "retrieved_examples": [],
                "llm_used": True,
            }

    detector.analyzer = Analyzer(memories)
    detector._retrieve_memory = lambda *args, **kwargs: memories
    detector._store_analysis_memory = lambda **kwargs: None

    result = detector.analyze_file(source_file)

    assert result["retrieved_memories"] == memories

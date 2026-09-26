from src.llm import demo
from src.memory.episodic_memory import EpisodicMemory
from src.memory.semantic_memory import SemanticMemory
from src.memory.short_term_memory import ShortTermMemory


def test_demo_saves_then_loads_memory_between_runs(tmp_path, monkeypatch):
    repository = tmp_path / "repository"
    repository.mkdir()
    created_detectors = []

    class Detector:
        def __init__(self):
            self.short_term_memory = ShortTermMemory()
            self.episodic_memory = EpisodicMemory()
            self.semantic_memory = SemanticMemory()
            created_detectors.append(self)

        def analyze_repository(self, _repository_path):
            self.short_term_memory.add("Prior analysis")
            self.episodic_memory.add_event("Analyzed repository")
            self.semantic_memory.add_fact("language", "Python")
            return {"repository": str(repository), "results": []}

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(demo, "RepositoryBugDetector", Detector)

    demo.analyze_repository(str(repository))
    demo.analyze_repository(str(repository))

    second_detector = created_detectors[1]
    assert "Prior analysis" in second_detector.short_term_memory.get_all()
    assert second_detector.episodic_memory.get_all()[0]["event"] == "Analyzed repository"
    assert second_detector.semantic_memory.get_fact("language")["value"] == "Python"
    assert (tmp_path / ".memory" / "short_term.json").exists()

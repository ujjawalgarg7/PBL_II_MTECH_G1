from src.dataset.bug_dataset_preprocessor import BugDatasetPreprocessor


def test_combine_files_uses_buggy_code_from_extractor():
    combined = BugDatasetPreprocessor._combine_files(
        [{"file": "example.py", "buggy_code": "broken = True"}]
    )

    assert "===== FILE: example.py =====" in combined
    assert "broken = True" in combined

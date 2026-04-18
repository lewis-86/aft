# tests/unit/test_observability_coverage.py
import pytest
from aft.observability.coverage import CoverageAnalyzer
from aft.observability.types import PRuleCoverageEntry


class TestCoverageAnalyzer:
    def test_analyze_known_rule_covered(self):
        analyzer = CoverageAnalyzer()
        test_names = ["test_violence_risk_score_0_8", "test_violence_risk_score_0_9"]
        result = analyzer.analyze(rule_files_changed=["rules/violence.yaml"], test_names=test_names)
        assert len(result) >= 1
        violence_entry = next((e for e in result if "violence" in e.rule), None)
        assert violence_entry is not None
        assert violence_entry.covered is True

    def test_analyze_no_matching_test(self):
        analyzer = CoverageAnalyzer()
        result = analyzer.analyze(rule_files_changed=["rules/spam.yaml"], test_names=["test_violence"])
        spam_entry = next((e for e in result if "spam" in e.rule), None)
        assert spam_entry is not None
        assert spam_entry.covered is False

    def test_analyze_empty_inputs(self):
        analyzer = CoverageAnalyzer()
        result = analyzer.analyze(rule_files_changed=[], test_names=[])
        assert result == []

    def test_analyze_multiple_rule_files(self):
        analyzer = CoverageAnalyzer()
        result = analyzer.analyze(
            rule_files_changed=["rules/violence.yaml", "rules/spam.yaml"],
            test_names=["test_violence_threshold", "test_spam_action"]
        )
        assert len(result) == 2
        violence = next(e for e in result if "violence" in e.rule)
        spam = next(e for e in result if "spam" in e.rule)
        assert violence.covered is True
        assert spam.covered is True
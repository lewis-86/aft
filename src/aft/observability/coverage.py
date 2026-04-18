"""Rule coverage analysis for AFT observability."""
from __future__ import annotations
from aft.observability.types import PRuleCoverageEntry


class CoverageAnalyzer:
    """Analyzes which policy rules have test coverage.

    Uses a simple heuristic: a rule file (e.g. "rules/violence.yaml")
    is considered covered if any test name contains a matching keyword.
    """

    # Keyword map: rule file segment -> test name keywords
    RULE_KEYWORDS = {
        "violence": ["violence", "violent"],
        "spam": ["spam"],
        "hate": ["hate", "hate_speech"],
        "adult": ["adult", "nudity", "nsfw"],
        "politics": ["politics", "political"],
        "misinfo": ["misinfo", "misinformation"],
        "dangerous": ["dangerous", "danger"],
        "copyright": ["copyright"],
    }

    def analyze(
        self,
        rule_files_changed: list[str],
        test_names: list[str],
    ) -> list[PRuleCoverageEntry]:
        """Analyze coverage for changed rule files against test names.

        Returns one PRuleCoverageEntry per changed rule file.
        """
        entries = []
        for filepath in rule_files_changed:
            rule_key = self._extract_rule_key(filepath)
            covered = self._is_covered(rule_key, test_names)
            matched_tests = [
                t for t in test_names
                if any(kw in t.lower() for kw in self.RULE_KEYWORDS.get(rule_key, [rule_key]))
            ]
            entries.append(PRuleCoverageEntry(
                rule=filepath,
                covered=covered,
                test_names=matched_tests,
            ))
        return entries

    def _extract_rule_key(self, filepath: str) -> str:
        """Extract a meaningful key from a rule file path."""
        import os
        basename = os.path.basename(filepath)
        name = os.path.splitext(basename)[0]
        return name.lower()

    def _is_covered(self, rule_key: str, test_names: list[str]) -> bool:
        keywords = self.RULE_KEYWORDS.get(rule_key, [rule_key])
        return any(
            any(kw in test_name.lower() for kw in keywords)
            for test_name in test_names
        )
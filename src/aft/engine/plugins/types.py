"""Types for test execution results."""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class TestCase:
    """Represents a single test case."""
    name: str
    description: str
    code: str
    expected_outcome: str = ""
    category: str = "policy"  # policy | model | api | e2e


@dataclass
class TestSuite:
    """Represents a collection of test cases."""
    test_cases: list[TestCase] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add(self, test_case: TestCase) -> None:
        self.test_cases.append(test_case)

    def to_pytest_code(self) -> str:
        """Render the test suite as pytest-compatible Python code."""
        lines = [
            '"""Auto-generated AFT test suite."""',
            'import pytest',
            '',
        ]
        for tc in self.test_cases:
            lines.append(f'def {tc.name}():')
            lines.append(f'    """{tc.description}"""')
            for line in tc.code.split('\n'):
                lines.append(f'    {line}')
            lines.append('')
        return '\n'.join(lines)


@dataclass
class TestResult:
    """Result of a single test execution."""
    name: str
    passed: bool
    duration_ms: float
    error_message: str = ""
    output: str = ""


@dataclass
class TestSuiteResult:
    """Result of a test suite execution."""
    suite_name: str
    results: list[TestResult] = field(default_factory=list)
    total_duration_ms: float = 0.0

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.passed)

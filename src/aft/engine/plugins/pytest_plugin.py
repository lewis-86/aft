"""pytest execution plugin for AFT."""
from __future__ import annotations
import tempfile
import subprocess
import time
from pathlib import Path
from aft.engine.plugins.types import TestSuite, TestSuiteResult, TestResult


class PytestPlugin:
    """Executes test suites using pytest."""

    def run_suite(self, suite: TestSuite, timeout: int = 300) -> TestSuiteResult:
        """Run a test suite and return results."""
        suite_name = suite.metadata.get("name", "aft_suite")
        result = TestSuiteResult(suite_name=suite_name)

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_aft_generated.py"
            test_file.write_text(suite.to_pytest_code())

            start_time = time.time()
            try:
                proc = subprocess.run(
                    ["python3", "-m", "pytest", str(test_file), "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=tmpdir,
                )
                duration_ms = (time.time() - start_time) * 1000
                result.total_duration_ms = duration_ms

                # Parse pytest output
                for line in proc.stdout.split('\n'):
                    if '::' in line and ('PASSED' in line or 'FAILED' in line):
                        # Format: /path/to/test_file.py::test_name PASSED [100%]
                        after_colons = line.split('::')[1]
                        name = after_colons.split()[0]
                        passed = 'PASSED' in line
                        result.results.append(TestResult(
                            name=name,
                            passed=passed,
                            duration_ms=duration_ms / max(len(result.results) + 1, 1),
                            output=line,
                        ))

                # If no results parsed, use return code
                if not result.results:
                    passed = proc.returncode == 0
                    result.results.append(TestResult(
                        name="suite_exec",
                        passed=passed,
                        duration_ms=duration_ms,
                        output=proc.stdout[-500:] if proc.stdout else "",
                        error_message=proc.stderr[-500:] if proc.stderr else "",
                    ))

            except subprocess.TimeoutExpired:
                result.total_duration_ms = timeout * 1000
                result.results.append(TestResult(
                    name="timeout",
                    passed=False,
                    duration_ms=timeout * 1000,
                    error_message=f"Test suite timed out after {timeout}s",
                ))
            except Exception as e:
                result.total_duration_ms = (time.time() - start_time) * 1000
                result.results.append(TestResult(
                    name="error",
                    passed=False,
                    duration_ms=result.total_duration_ms,
                    error_message=str(e),
                ))

        return result

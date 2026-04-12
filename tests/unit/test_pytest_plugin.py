import pytest
import tempfile
import os
from aft.engine.plugins.pytest_plugin import PytestPlugin
from aft.engine.plugins.types import PolicyTestSuite as TestSuite, PolicyTestCase as TestCase


class TestPytestPlugin:
    def test_run_suite_executes_tests(self):
        plugin = PytestPlugin()
        suite = TestSuite(metadata={"name": "test_sample"})
        suite.add(TestCase(
            name="test_basic_pass",
            description="A basic passing test",
            code='def test_basic_pass():\n    assert True',
        ))
        result = plugin.run_suite(suite)
        assert result.passed_count == 1
        assert result.failed_count == 0

    def test_run_suite_catches_failures(self):
        plugin = PytestPlugin()
        suite = TestSuite(metadata={"name": "test_fail"})
        suite.add(TestCase(
            name="test_basic_fail",
            description="A basic failing test",
            code='def test_basic_fail():\n    assert False, "expected failure"',
        ))
        result = plugin.run_suite(suite)
        assert result.failed_count >= 1
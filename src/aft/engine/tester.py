"""Test execution engine interface."""
from __future__ import annotations
from abc import ABC, abstractmethod
from aft.engine.plugins.types import TestSuite, TestSuiteResult


class Tester(ABC):
    """Abstract base class for test execution plugins."""

    @abstractmethod
    def run_suite(self, suite: TestSuite, timeout: int = 300) -> TestSuiteResult:
        """Execute a test suite and return results."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the plugin name."""
        pass

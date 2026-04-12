# tests/unit/test_observability_store.py
import pytest
import tempfile
import os
import json
from pathlib import Path
from aft.observability.store import ObservabilityStore
from aft.observability.types import PRObservationData


class TestObservabilityStore:
    def test_save_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ObservabilityStore(data_dir=tmpdir)
            obs = PRObservationData(
                pr_number=42,
                repo="tiktok/content-safety",
                branch="feat/test",
                author="tester",
                test_result={"passed": 3, "failed": 0, "skipped": 0, "duration_ms": 400},
                coverage={"rules_total": 47, "rules_covered": 38, "coverage_ratio": 0.809},
            )
            path = store.save(obs)
            assert path.exists()
            data = json.loads(path.read_text())
            assert data["pr_number"] == 42
            assert data["coverage"]["coverage_ratio"] == 0.809

    def test_load_reads_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ObservabilityStore(data_dir=tmpdir)
            obs = PRObservationData(
                pr_number=99,
                repo="test/repo",
                branch="main",
                author="u",
                test_result={"passed": 1, "failed": 0, "skipped": 0, "duration_ms": 50},
                coverage={"rules_total": 10, "rules_covered": 5, "coverage_ratio": 0.5},
            )
            store.save(obs)
            loaded = store.load(99)
            assert loaded.pr_number == 99
            assert loaded.coverage["coverage_ratio"] == 0.5

    def test_load_history_returns_recent_runs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ObservabilityStore(data_dir=tmpdir)
            for i in range(7):
                obs = PRObservationData(
                    pr_number=100 + i,
                    repo="test/repo",
                    branch="main",
                    author="u",
                    test_result={"passed": i, "failed": 0, "skipped": 0, "duration_ms": 100 * i},
                    coverage={"rules_total": 10, "rules_covered": i, "coverage_ratio": i / 10},
                )
                store.save(obs)
            history = store.load_history(limit=5)
            assert len(history) == 5
            # Most recent first
            assert history[0].pr_number == 106

    def test_load_history_empty_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ObservabilityStore(data_dir=tmpdir)
            history = store.load_history(limit=5)
            assert history == []

    def test_data_dir_created_if_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ObservabilityStore(data_dir=f"{tmpdir}/nested/data")
            assert Path(f"{tmpdir}/nested/data").exists()
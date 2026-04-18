"""Observability data store — reads/writes data/pr-{n}.json files."""
from __future__ import annotations
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aft.observability.types import PRObservationData


class ObservabilityStore:
    """Stores and retrieves AFT observation records as JSON files."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self._ensure_data_dir()

    def _ensure_data_dir(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _file_path(self, pr_number: int) -> Path:
        return self.data_dir / f"pr-{pr_number}.json"

    def save(self, obs: "PRObservationData") -> Path:
        """Save an observation record to JSON.

        Returns the Path of the saved file.
        """
        self._ensure_data_dir()
        # Stamp timestamp if not set
        if not obs.timestamp:
            obs.timestamp = datetime.now(timezone.utc).isoformat()
        path = self._file_path(obs.pr_number)
        data = self._to_dict(obs)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return path

    def load(self, pr_number: int) -> "PRObservationData":
        """Load an observation record by PR number."""
        path = self._file_path(pr_number)
        if not path.exists():
            raise FileNotFoundError(f"No observation for PR {pr_number}")
        data = json.loads(path.read_text())
        return self._from_dict(data)

    def load_history(self, limit: int = 5) -> list["PRObservationData"]:
        """Load the most recent `limit` observation records, sorted newest-first."""
        self._ensure_data_dir()
        files = sorted(
            self.data_dir.glob("pr-*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        results = []
        for f in files[:limit]:
            try:
                data = json.loads(f.read_text())
                results.append(self._from_dict(data))
            except (json.JSONDecodeError, KeyError):
                continue
        return results

    def load_recent(self, hours: int = 24) -> list["PRObservationData"]:
        """Load observations from the last N hours."""
        self._ensure_data_dir()
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        files = sorted(
            self.data_dir.glob("pr-*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        results = []
        for f in files:
            try:
                data = json.loads(f.read_text())
                ts = datetime.fromisoformat(data.get("timestamp", "1970-01-01T00:00:00Z").replace("Z", "+00:00"))
                if ts >= cutoff:
                    results.append(self._from_dict(data))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        return results

    def load_previous_period(self, days: int = 7, offset: int = 0) -> list["PRObservationData"]:
        """Load observations from a historical period (before the last N days).

        Args:
            days: number of days in the period
            offset: how many days to go back before the "last days" boundary
                   e.g. offset=7 means "7-14 days ago"
        """
        self._ensure_data_dir()
        now = datetime.now(timezone.utc)
        end_cutoff = now - timedelta(days=offset)
        start_cutoff = end_cutoff - timedelta(days=days)
        files = sorted(
            self.data_dir.glob("pr-*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        results = []
        for f in files:
            try:
                data = json.loads(f.read_text())
                ts = datetime.fromisoformat(data.get("timestamp", "1970-01-01T00:00:00Z").replace("Z", "+00:00"))
                if start_cutoff <= ts < end_cutoff:
                    results.append(self._from_dict(data))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        return results

    def _to_dict(self, obs: "PRObservationData") -> dict:
        return {
            "pr_number": obs.pr_number,
            "repo": obs.repo,
            "branch": obs.branch,
            "author": obs.author,
            "timestamp": obs.timestamp,
            "rule_files_changed": obs.rule_files_changed,
            "test_result": obs.test_result,
            "coverage": obs.coverage,
            "rule_coverage": [
                {"rule": e.rule, "covered": e.covered, "test_names": e.test_names}
                for e in obs.rule_coverage
            ],
            "self_healed": obs.self_healed,
            "risk_assessment": obs.risk_assessment,
            "trend_reference": obs.trend_reference,
        }

    def _from_dict(self, data: dict) -> "PRObservationData":
        from aft.observability.types import PRObservationData, PRuleCoverageEntry
        rule_coverage = [
            PRuleCoverageEntry(
                rule=e["rule"],
                covered=e["covered"],
                test_names=e.get("test_names", []),
            )
            for e in data.get("rule_coverage", [])
        ]
        return PRObservationData(
            pr_number=data["pr_number"],
            repo=data["repo"],
            branch=data["branch"],
            author=data["author"],
            timestamp=data.get("timestamp", ""),
            rule_files_changed=data.get("rule_files_changed", []),
            test_result=data.get("test_result", {}),
            coverage=data.get("coverage", {}),
            rule_coverage=rule_coverage,
            self_healed=data.get("self_healed", False),
            risk_assessment=data.get("risk_assessment", ""),
            trend_reference=data.get("trend_reference", ""),
        )
# src/aft/cli/router.py
"""DiffRouter — parses combined diff, routes to appropriate analyzers."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
import re


@dataclass
class RuleFileChange:
    """A rule.yaml file change."""
    rule_id: str
    diff: str
    before: dict = field(default_factory=dict)
    after: dict = field(default_factory=dict)
    changed_fields: List[str] = field(default_factory=list)


@dataclass
class SkillFileChange:
    """A SKILL.md file change."""
    skill_name: str
    diff: str
    file_path: str


@dataclass
class CodeChange:
    """A source code file change."""
    file_path: str
    diff: str


@dataclass
class DiffRouterResult:
    """Result of routing a combined diff."""
    rule_changes: List[RuleFileChange] = field(default_factory=list)
    skill_changes: List[SkillFileChange] = field(default_factory=list)
    code_changes: List[CodeChange] = field(default_factory=list)
    change_types: List[str] = field(default_factory=list)


class DiffRouter:
    """Parses combined diff and routes files to appropriate analyzers."""

    RULE_FILE_RE = re.compile(r"^\+\+\+ b/rules/([^/]+)/rule\.yaml$", re.MULTILINE)
    SKILL_FILE_RE = re.compile(r"^\+\+\+ b/fixtures/.*\.md$", re.MULTILINE)
    RULE_DESIGN_RE = re.compile(r"^\+\+\+ b/rules/([^/]+)/DESIGN\.md$", re.MULTILINE)
    RULE_TS_RE = re.compile(r"^\+\+\+ b/src/lint/rules/([^/]+)\.ts$", re.MULTILINE)
    CODE_TS_RE = re.compile(r"^\+\+\+ b/src/", re.MULTILINE)

    def __init__(self, diff: str):
        self.diff = diff

    def route(self) -> DiffRouterResult:
        """Parse the diff and categorize changes."""
        result = DiffRouterResult()

        # Split diff into per-file diffs
        file_diffs = self._split_file_diffs()

        for file_path, file_diff in file_diffs.items():
            if self._is_rule_yaml(file_path):
                rule_id = self._extract_rule_id(file_path)
                changed_fields = self._extract_changed_fields(file_diff)
                result.rule_changes.append(RuleFileChange(
                    rule_id=rule_id,
                    diff=file_diff,
                    changed_fields=changed_fields,
                ))
            elif self._is_skill_md(file_path):
                skill_name = self._extract_skill_name(file_diff)
                result.skill_changes.append(SkillFileChange(
                    skill_name=skill_name,
                    diff=file_diff,
                    file_path=file_path,
                ))
            elif self._is_code_file(file_path):
                result.code_changes.append(CodeChange(
                    file_path=file_path,
                    diff=file_diff,
                ))

        # Build change_types
        if result.rule_changes:
            result.change_types.append("rule")
        if result.skill_changes:
            result.change_types.append("skill")
        if result.code_changes:
            result.change_types.append("code")

        return result

    def _split_file_diffs(self) -> dict:
        """Split combined diff into per-file diffs."""
        files = {}
        current_file = None
        current_diff = []

        for line in self.diff.splitlines(keepends=True):
            if line.startswith("--- ") or line.startswith("+++ ") or line.startswith("@@ "):
                if current_file is not None:
                    files[current_file] = "".join(current_diff)
                # Extract file path from +++ b/path
                match = re.match(r"^\+\+\+ b/(.+)$", line.strip())
                if match:
                    current_file = match.group(1)
                current_diff = [line]
            else:
                current_diff.append(line)

        if current_file is not None and current_diff:
            files[current_file] = "".join(current_diff)

        return files

    def _is_rule_yaml(self, path: str) -> bool:
        return bool(re.search(r"rules/[^/]+/rule\.yaml$", path))

    def _is_skill_md(self, path: str) -> bool:
        return path.endswith(".md") and ("fixtures/" in path or "skills/" in path)

    def _is_code_file(self, path: str) -> bool:
        return path.startswith("src/")

    def _extract_rule_id(self, path: str) -> str:
        match = re.search(r"rules/([^/]+)/rule\.yaml$", path)
        return match.group(1) if match else "unknown"

    def _extract_changed_fields(self, diff: str) -> List[str]:
        """Extract YAML field names that changed (simple heuristic)."""
        fields = set()
        for line in diff.splitlines():
            if line.startswith("-") or line.startswith("+"):
                stripped = line[1:].strip()
                if ":" in stripped and not stripped.startswith("#"):
                    field_name = stripped.split(":")[0].strip()
                    if field_name and not field_name.startswith("-"):
                        fields.add(field_name)
        return list(fields)

    def _extract_skill_name(self, diff: str) -> str:
        """Extract skill name from frontmatter in diff."""
        match = re.search(r"^\+name:\s*(.+)$", diff, re.MULTILINE)
        return match.group(1).strip() if match else "unknown"
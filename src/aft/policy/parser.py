"""Policy rule change parser."""
from __future__ import annotations
from dataclasses import dataclass
import re


@dataclass
class RuleChange:
    """Represents a single change in a policy rule."""
    field: str
    old_value: str
    new_value: str
    file_path: str = ""


class PolicyRuleParser:
    """Parses diff/patch format to extract rule changes."""

    DIFF_HUNK_REGEX = re.compile(r'^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@', re.MULTILINE)
    FILE_PATH_REGEX = re.compile(r'^\+\+\+ b/(.+)$', re.MULTILINE)
    LINE_CHANGE_REGEX = re.compile(r'^([+\-])(\s*|)(.+)$', re.MULTILINE)

    def parse_diff(self, diff: str) -> list[RuleChange]:
        """Parse a unified diff and extract field-level changes."""
        changes = []
        lines = diff.split('\n')
        current_file = ""

        i = 0
        while i < len(lines):
            line = lines[i]

            # Track file path
            if line.startswith('+++'):
                match = self.FILE_PATH_REGEX.match(line)
                if match:
                    current_file = match.group(1)

            # Parse line changes
            if line.startswith('-') and not line.startswith('---'):
                old_line = line.lstrip('-').strip()
                new_line = ""
                # Look ahead for corresponding + line
                if i + 1 < len(lines) and lines[i + 1].startswith('+'):
                    i += 1
                    new_line = lines[i].lstrip('+').strip()

                field, old_val, new_val = self._extract_field_value(old_line, new_line)
                if field:
                    changes.append(RuleChange(
                        field=field,
                        old_value=old_val,
                        new_value=new_val,
                        file_path=current_file,
                    ))
            i += 1

        return changes

    def _extract_field_value(self, old_line: str, new_line: str) -> tuple[str, str, str]:
        """Extract field name and values from a line or line pair."""
        if ':' in old_line:
            parts = old_line.split(':', 1)
            field = parts[0].strip()
            old_val = parts[1].strip() if len(parts) > 1 else ""
            new_val = new_line.split(':', 1)[1].strip() if ':' in new_line and new_line else old_val
            return field, old_val, new_val

        if '=' in old_line:
            parts = old_line.split('=', 1)
            field = parts[0].strip()
            old_val = parts[1].strip() if len(parts) > 1 else ""
            new_val = new_line.split('=', 1)[1].strip() if '=' in new_line and new_line else old_val
            return field, old_val, new_val

        return "", "", ""
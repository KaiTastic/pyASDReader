#!/usr/bin/env python3
"""
CHANGELOG.md manager for pyASDReader.

Handles moving content from [Unreleased] to versioned sections.
Uses structured parsing instead of fragile regex patterns.
"""

import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional, Tuple


class ChangelogManager:
    """Manages CHANGELOG.md updates for releases."""

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize changelog manager.

        Args:
            project_root: Path to project root. If None, auto-detect.
        """
        if project_root is None:
            self.project_root = Path(__file__).parent.parent.parent
        else:
            self.project_root = Path(project_root)

        self.changelog_path = self.project_root / "CHANGELOG.md"

    def read_changelog(self) -> str:
        """Read CHANGELOG.md content."""
        if not self.changelog_path.exists():
            raise FileNotFoundError(f"CHANGELOG.md not found at {self.changelog_path}")

        with open(self.changelog_path, 'r', encoding='utf-8') as f:
            return f.read()

    def write_changelog(self, content: str):
        """Write content to CHANGELOG.md."""
        with open(self.changelog_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def extract_unreleased_content(self, content: str) -> Tuple[Optional[str], Optional[int], Optional[int]]:
        """
        Extract [Unreleased] section content.

        Returns:
            Tuple of (content, start_pos, end_pos) or (None, None, None) if not found
        """
        # Find [Unreleased] header
        unreleased_pattern = r'##\s+\[Unreleased\]'
        match = re.search(unreleased_pattern, content)

        if not match:
            return None, None, None

        start = match.end()

        # Find next ## header or end of file
        next_header_pattern = r'\n##\s+\['
        next_match = re.search(next_header_pattern, content[start:])

        if next_match:
            end = start + next_match.start()
        else:
            end = len(content)

        unreleased_content = content[start:end].strip()

        return unreleased_content, match.start(), end

    def has_meaningful_content(self, content: str) -> bool:
        """
        Check if content has meaningful changes (not just empty sections).

        Args:
            content: Content to check

        Returns:
            True if has meaningful content, False otherwise
        """
        # Remove common section headers
        content_without_headers = re.sub(
            r'###\s+(Added|Changed|Deprecated|Removed|Fixed|Security)\s*\n',
            '',
            content
        )

        # Check if there's substantial content left
        content_cleaned = content_without_headers.strip()

        # Must have at least one bullet point or meaningful text
        has_bullets = '-' in content_cleaned or '*' in content_cleaned
        has_text = len(content_cleaned) > 20  # More than just whitespace

        return has_bullets and has_text

    def move_unreleased_to_version(
        self,
        version: str,
        release_date: Optional[str] = None
    ) -> bool:
        """
        Move [Unreleased] content to a new versioned section.

        Args:
            version: Version number (e.g., "1.2.3")
            release_date: Release date in YYYY-MM-DD format. If None, uses today.

        Returns:
            True if successful, False otherwise
        """
        if release_date is None:
            release_date = date.today().strftime("%Y-%m-%d")

        # Read current content
        content = self.read_changelog()

        # Extract unreleased content
        unreleased, start_pos, end_pos = self.extract_unreleased_content(content)

        if unreleased is None:
            print("Error: [Unreleased] section not found in CHANGELOG.md")
            return False

        if not unreleased.strip():
            print("Warning: [Unreleased] section is empty")
            print("Please add release notes before releasing")
            return False

        if not self.has_meaningful_content(unreleased):
            print("Warning: [Unreleased] section has no meaningful content")
            print("Please add actual changes (bullet points) before releasing")
            return False

        # Build new content
        # 1. Keep everything before [Unreleased]
        before_unreleased = content[:start_pos]

        # 2. Create empty [Unreleased] section
        new_unreleased = "## [Unreleased]\n\n"

        # 3. Create new version section with the content
        new_version_section = f"## [{version}] - {release_date}\n\n{unreleased}\n\n"

        # 4. Keep everything after old [Unreleased] section
        after_unreleased = content[end_pos:]

        # Combine
        new_content = before_unreleased + new_unreleased + new_version_section + after_unreleased

        # Write back
        self.write_changelog(new_content)

        print("Updated CHANGELOG.md:")
        print(f"  - Moved {len(unreleased)} characters from [Unreleased]")
        print(f"  - Created section [{version}] - {release_date}")

        return True

    def verify_version_not_exists(self, version: str) -> bool:
        """
        Verify that version doesn't already exist in CHANGELOG.

        Args:
            version: Version to check

        Returns:
            True if version doesn't exist, False if it does
        """
        content = self.read_changelog()
        pattern = rf'##\s+\[{re.escape(version)}\]'

        if re.search(pattern, content):
            print(f"Error: Version [{version}] already exists in CHANGELOG.md")
            return False

        return True

    def get_version_content(self, version: str) -> Optional[str]:
        """
        Extract content for a specific version.

        Args:
            version: Version number to extract

        Returns:
            Version content or None if not found
        """
        content = self.read_changelog()

        # Find version header
        version_pattern = rf'##\s+\[{re.escape(version)}\]\s+-\s+\d{{4}}-\d{{2}}-\d{{2}}'
        match = re.search(version_pattern, content)

        if not match:
            return None

        start = match.end()

        # Find next ## header or end of file
        next_header_pattern = r'\n##\s+\['
        next_match = re.search(next_header_pattern, content[start:])

        if next_match:
            end = start + next_match.start()
        else:
            end = len(content)

        return content[start:end].strip()


def main():
    """CLI entry point for changelog manager."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python changelog_manager.py release <version> [date]")
        print("  python changelog_manager.py get <version>")
        print()
        print("Examples:")
        print("  python changelog_manager.py release 1.2.3")
        print("  python changelog_manager.py release 1.2.3 2025-10-07")
        print("  python changelog_manager.py get 1.2.3")
        sys.exit(1)

    command = sys.argv[1]
    manager = ChangelogManager()

    if command == "release":
        if len(sys.argv) < 3:
            print("Error: Version required for release command")
            sys.exit(1)

        version = sys.argv[2]
        release_date = sys.argv[3] if len(sys.argv) > 3 else None

        # Verify version doesn't already exist
        if not manager.verify_version_not_exists(version):
            sys.exit(1)

        # Move unreleased to version
        if manager.move_unreleased_to_version(version, release_date):
            print()
            print(f"Successfully prepared CHANGELOG for version {version}")
            sys.exit(0)
        else:
            print()
            print("Failed to update CHANGELOG")
            sys.exit(1)

    elif command == "get":
        if len(sys.argv) < 3:
            print("Error: Version required for get command")
            sys.exit(1)

        version = sys.argv[2]
        content = manager.get_version_content(version)

        if content:
            print(content)
            sys.exit(0)
        else:
            print(f"Error: Version {version} not found in CHANGELOG")
            sys.exit(1)

    else:
        print(f"Error: Unknown command: {command}")
        print("Valid commands: release, get")
        sys.exit(1)


if __name__ == "__main__":
    main()

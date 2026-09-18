#!/usr/bin/env python3
"""
Pre-release validation script for pyASDReader.

Checks various conditions before allowing a release to proceed.
Can be run manually or in CI/CD pipelines.
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional
from packaging import version as pkg_version


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class ReleaseValidator:
    """Validates project state before release."""

    def __init__(self, project_root: Path = None, strict: bool = False, strict_semantic: bool = False):
        """
        Initialize validator.

        Args:
            project_root: Project root path. If None, auto-detect.
            strict: If True, treat all warnings as errors (legacy mode).
            strict_semantic: If True, only enforce strict semantic versioning checks.
        """
        if project_root is None:
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)

        self.strict = strict
        self.strict_semantic = strict_semantic
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.semantic_warnings: List[str] = []  # Warnings specific to semantic versioning

    def check_git_status(self) -> bool:
        """
        Check git working directory is clean.

        Returns:
            True if clean, False otherwise
        """
        try:
            result = subprocess.run(
                ['git', 'diff-index', '--quiet', 'HEAD', '--'],
                cwd=self.project_root,
                capture_output=True
            )
            if result.returncode != 0:
                self.warnings.append(
                    "Git working directory has uncommitted changes. "
                    "Consider committing or stashing before release."
                )
                return False
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.warnings.append("Could not check git status (git not available?)")
            return False

    def check_on_correct_branch(self, expected_branch: str = 'dev') -> bool:
        """
        Check if on the expected branch.

        Args:
            expected_branch: Expected branch name

        Returns:
            True if on correct branch, False otherwise
        """
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            current_branch = result.stdout.strip()

            if current_branch != expected_branch:
                self.warnings.append(
                    f"Current branch is '{current_branch}', expected '{expected_branch}'. "
                    "Releases should typically be initiated from 'dev' branch."
                )
                return False
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.warnings.append("Could not check current branch")
            return False

    def check_changelog_has_content(self) -> bool:
        """
        Check CHANGELOG.md has meaningful content in [Unreleased].

        Returns:
            True if has content, False otherwise
        """
        changelog_path = self.project_root / "CHANGELOG.md"

        if not changelog_path.exists():
            self.errors.append("CHANGELOG.md not found")
            return False

        with open(changelog_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find [Unreleased] section
        unreleased_pattern = r'##\s+\[Unreleased\](.*?)##\s+\['
        match = re.search(unreleased_pattern, content, re.DOTALL)

        if not match:
            self.errors.append("[Unreleased] section not found in CHANGELOG.md")
            return False

        unreleased_content = match.group(1).strip()

        if not unreleased_content:
            self.errors.append(
                "[Unreleased] section in CHANGELOG.md is empty. "
                "Please add release notes before releasing."
            )
            return False

        # Check for meaningful content (bullet points)
        has_bullets = '-' in unreleased_content or '*' in unreleased_content

        if not has_bullets:
            self.errors.append(
                "[Unreleased] section has no bullet points. "
                "Please document your changes before releasing."
            )
            return False

        # Store unreleased content for semantic check
        self.unreleased_content = unreleased_content

        return True

    def check_changelog_matches_version_type(self, version_type: str) -> bool:
        """
        Check if CHANGELOG content matches the semantic version type.

        Args:
            version_type: 'patch', 'minor', or 'major'

        Returns:
            True if matches or check not applicable, False with warning otherwise
        """
        if not hasattr(self, 'unreleased_content'):
            # check_changelog_has_content() must be called first
            return True

        content = self.unreleased_content

        # Detect sections in CHANGELOG
        has_added = '### Added' in content or '###Added' in content
        has_changed = '### Changed' in content or '###Changed' in content
        has_deprecated = '### Deprecated' in content or '###Deprecated' in content
        has_removed = '### Removed' in content or '###Removed' in content
        has_fixed = '### Fixed' in content or '###Fixed' in content
        has_security = '### Security' in content or '###Security' in content

        # Semantic versioning guidelines check
        # Store warnings separately for flexible handling
        if version_type == 'patch':
            # Patch should typically only have fixes or security updates
            if has_added or has_changed or has_deprecated or has_removed:
                self.semantic_warnings.append(
                    f"Version type is 'patch' but CHANGELOG contains new features or changes. "
                    f"Consider using 'minor' or 'major' instead for semantic versioning compliance."
                )
                return False

        elif version_type == 'minor':
            # Minor can have new features but no breaking changes
            if has_removed or has_deprecated:
                self.semantic_warnings.append(
                    f"Version type is 'minor' but CHANGELOG contains removals or deprecations. "
                    f"This might indicate breaking changes. Consider 'major' if backwards compatibility is broken."
                )
                return False

            if not (has_added or has_changed):
                self.semantic_warnings.append(
                    f"Version type is 'minor' but no new features (Added/Changed) in CHANGELOG. "
                    f"Consider 'patch' if only fixes were made."
                )
                return False

        elif version_type == 'major':
            # Major should indicate significant changes
            if not (has_removed or has_deprecated or has_changed):
                self.semantic_warnings.append(
                    f"Version type is 'major' but no breaking changes indicated in CHANGELOG. "
                    f"Major versions typically include significant changes, removals, or deprecations. "
                    f"Consider 'minor' if backwards compatible."
                )
                return False

        return True

    def check_tests_exist(self) -> bool:
        """
        Check test directory exists and has tests.

        Returns:
            True if tests exist, False otherwise
        """
        tests_dir = self.project_root / "tests"

        if not tests_dir.exists():
            self.warnings.append("tests/ directory not found")
            return False

        test_files = list(tests_dir.glob("test_*.py"))

        if not test_files:
            self.warnings.append("No test files found in tests/ directory")
            return False

        return True

    def run_tests(self) -> bool:
        """
        Run pytest test suite.

        Returns:
            True if tests pass, False otherwise
        """
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', 'tests/', '-v'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            if result.returncode != 0:
                self.errors.append(
                    f"Tests failed. Please fix failing tests before releasing.\n"
                    f"Output:\n{result.stdout}\n{result.stderr}"
                )
                return False

            return True

        except FileNotFoundError:
            self.warnings.append("pytest not found. Skipping tests.")
            return False
        except subprocess.TimeoutExpired:
            self.errors.append("Tests timed out after 5 minutes")
            return False

    def check_version_consistency(self) -> bool:
        """
        Check version consistency across files.
        Focuses on fallback versions which should be consistent.

        Returns:
            True if consistent or acceptable, False otherwise
        """
        # Check fallback version consistency between pyproject.toml and _version.py
        pyproject_path = self.project_root / "pyproject.toml"
        version_py_path = self.project_root / "src" / "_version.py"

        fallback_versions = {}

        # Extract from pyproject.toml
        if pyproject_path.exists():
            with open(pyproject_path, 'r', encoding='utf-8') as f:
                content = f.read()
            match = re.search(r'fallback_version\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                fallback_versions['pyproject.toml'] = match.group(1)

        # Extract from _version.py (fallback)
        if version_py_path.exists():
            with open(version_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Look for the fallback version in except block
            match = re.search(r'except[^:]*:\s*(?:#[^\n]*\n)*\s*__version__\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
            if match:
                fallback_versions['src/_version.py'] = match.group(1)

        # Check consistency
        if len(fallback_versions) >= 2:
            unique_versions = set(fallback_versions.values())
            if len(unique_versions) > 1:
                self.errors.append(
                    "Fallback versions are inconsistent:\n" +
                    "\n".join(f"  {k}: {v}" for k, v in fallback_versions.items()) +
                    "\n\nFallback versions MUST match across all files. " +
                    "They should be '0.0.0' for uninitialized/non-git environments."
                )
                return False

            # Check if fallback is "0.0.0" (recommended)
            if list(unique_versions)[0] != "0.0.0":
                self.warnings.append(
                    f"Fallback version is '{list(unique_versions)[0]}', recommended: '0.0.0'\n" +
                    "Fallback version indicates uninitialized/non-git environment and should typically be 0.0.0."
                )

        return True

    def check_required_files_exist(self) -> bool:
        """
        Check all required project files exist.

        Returns:
            True if all exist, False otherwise
        """
        required_files = [
            "README.md",
            "CHANGELOG.md",
            "pyproject.toml",
            "LICENSE",
            "src/__init__.py",
        ]

        missing = []
        for file in required_files:
            if not (self.project_root / file).exists():
                missing.append(file)

        if missing:
            self.errors.append(f"Required files missing: {', '.join(missing)}")
            return False

        return True

    def get_latest_git_tag(self) -> Optional[str]:
        """
        Get the latest git tag version.

        Returns:
            Latest tag version string, or None if no tags exist
        """
        try:
            result = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                tag = result.stdout.strip()
                # Remove 'v' prefix if present
                return tag.lstrip('v')
            return None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def check_version_increment(self, new_version: str) -> bool:
        """
        Check if new version is greater than current version.

        Args:
            new_version: Proposed new version (e.g., "1.2.3")

        Returns:
            True if version increment is valid, False otherwise
        """
        current_version_str = self.get_latest_git_tag()

        if current_version_str is None:
            # No existing tags, any version is acceptable
            return True

        try:
            current = pkg_version.parse(current_version_str)
            new = pkg_version.parse(new_version)

            if new <= current:
                self.errors.append(
                    f"Version must increase: current={current_version_str}, proposed={new_version}. "
                    f"New version must be greater than current version."
                )
                return False

            # Check if increment follows semantic versioning
            current_parts = [int(x) for x in current_version_str.split('.')]
            new_parts = [int(x) for x in new_version.split('.')]

            # Pad to same length
            while len(current_parts) < 3:
                current_parts.append(0)
            while len(new_parts) < 3:
                new_parts.append(0)

            major_inc = new_parts[0] - current_parts[0]
            minor_inc = new_parts[1] - current_parts[1]
            patch_inc = new_parts[2] - current_parts[2]

            # Check for valid increment pattern
            if major_inc > 1 or minor_inc > 1 or patch_inc > 1:
                self.warnings.append(
                    f"Version jump seems large: {current_version_str} → {new_version}. "
                    f"Consider incremental versioning."
                )

            if major_inc == 1 and (new_parts[1] != 0 or new_parts[2] != 0):
                self.warnings.append(
                    f"Major version bump should reset minor and patch to 0: {new_version}"
                )

            if major_inc == 0 and minor_inc == 1 and new_parts[2] != 0:
                self.warnings.append(
                    f"Minor version bump should reset patch to 0: {new_version}"
                )

            return True

        except Exception as e:
            self.warnings.append(f"Could not parse version numbers: {e}")
            return True  # Don't fail on parsing errors

    def validate_all(self, run_tests: bool = True, version_type: str = None, new_version: str = None) -> Tuple[bool, List[str], List[str]]:
        """
        Run all validation checks.

        Args:
            run_tests: Whether to run test suite (can be slow)
            version_type: Version type ('patch', 'minor', 'major') for semantic check
            new_version: New version to validate (e.g., "1.2.3")

        Returns:
            Tuple of (success, errors, warnings)
        """
        print("Running pre-release validation checks...")
        print()

        # Critical checks (errors)
        print("[1/9] Checking required files exist...")
        self.check_required_files_exist()

        print("[2/9] Checking CHANGELOG content...")
        self.check_changelog_has_content()

        # Version increment check (if new version provided)
        if new_version:
            print(f"[3/9] Checking version increment: {new_version}...")
            self.check_version_increment(new_version)
        else:
            print("[3/9] Skipping version increment check (no new version provided)")

        # Semantic version check (if version type provided)
        if version_type and version_type in ['patch', 'minor', 'major']:
            print(f"[4/9] Checking CHANGELOG matches version type '{version_type}'...")
            self.check_changelog_matches_version_type(version_type)
        else:
            print("[4/9] Skipping semantic version check (no version type provided)")

        # Warning checks
        print("[5/9] Checking git status...")
        self.check_git_status()

        print("[6/9] Checking current branch...")
        self.check_on_correct_branch()

        print("[7/9] Checking version consistency (informational)...")
        self.check_version_consistency()

        print("[8/9] Checking tests exist...")
        self.check_tests_exist()

        # Optional test run
        if run_tests:
            print("[9/9] Running test suite...")
            self.run_tests()
        else:
            print("[9/9] Skipping test suite (use --run-tests to enable)")

        print()

        # Determine overall result
        has_errors = len(self.errors) > 0
        has_warnings = len(self.warnings) > 0
        has_semantic_warnings = len(self.semantic_warnings) > 0

        # Handle strict modes
        if self.strict_semantic and has_semantic_warnings:
            # Only semantic warnings become errors
            self.errors.extend(self.semantic_warnings)
            self.semantic_warnings = []
            has_errors = True
        elif self.strict and (has_warnings or has_semantic_warnings):
            # All warnings become errors
            self.errors.extend(self.warnings)
            self.errors.extend(self.semantic_warnings)
            self.warnings = []
            self.semantic_warnings = []
            has_errors = True
        else:
            # Merge semantic warnings with regular warnings for display
            self.warnings.extend(self.semantic_warnings)

        success = not has_errors

        return success, self.errors, self.warnings


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate project state before release"
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help="Treat warnings as errors"
    )
    parser.add_argument(
        '--run-tests',
        action='store_true',
        help="Run full test suite (slower)"
    )
    parser.add_argument(
        '--no-tests',
        action='store_true',
        help="Skip test suite entirely"
    )
    parser.add_argument(
        '--version-type',
        choices=['patch', 'minor', 'major'],
        help="Version type for semantic versioning check (patch/minor/major)"
    )
    parser.add_argument(
        '--new-version',
        type=str,
        help="New version to validate (e.g., 1.2.3)"
    )

    args = parser.parse_args()

    validator = ReleaseValidator(strict=args.strict)

    run_tests = args.run_tests and not args.no_tests

    success, errors, warnings = validator.validate_all(
        run_tests=run_tests,
        version_type=args.version_type,
        new_version=args.new_version
    )

    # Print results
    if errors:
        print("ERRORS:")
        for error in errors:
            print(f"  - {error}")
        print()

    if warnings:
        print("WARNINGS:")
        for warning in warnings:
            print(f"  - {warning}")
        print()

    if success:
        print("Validation passed!")
        print()
        if warnings and not args.strict:
            print("Note: Warnings present but allowed in non-strict mode")
        sys.exit(0)
    else:
        print("Validation failed!")
        print()
        print("Please fix the errors above before releasing.")
        sys.exit(1)


if __name__ == "__main__":
    main()

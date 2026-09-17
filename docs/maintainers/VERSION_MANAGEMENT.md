# Version Management Guide

> **📚 New Documentation Structure**: This guide has been reorganized for better clarity.
> - **This file**: Quick reference and core workflows
> - **[CI/CD workflows](CI_CD_WORKFLOWS.md)**: Detailed CI/CD pipeline information
> - **[Release examples](RELEASE_EXAMPLES.md)**: Step-by-step release scenarios

## Overview

pyASDReader uses **setuptools_scm** for automatic version management based on Git tags. This ensures version consistency across:
- Local development environment
- PyPI packages
- GitHub releases

### Release Tools

Python-based tools for improved cross-platform compatibility:

```bash
# Validate release readiness (strict mode enforces semantic versioning)
python scripts/validate_release.py --run-tests --strict

# Manage CHANGELOG.md structure
python scripts/utils/changelog_manager.py release 1.2.4
```

These tools are automatically used by `scripts/release.sh` with strict mode enabled by default.

**Note**: Version numbers are automatically managed by setuptools_scm from Git tags. No manual version file editing is needed.

**Semantic Versioning Enforcement**: The release script now enforces semantic versioning rules in strict mode:
- **Patch releases** (1.2.3 → 1.2.4): Only fixes and security updates allowed
- **Minor releases** (1.2.3 → 1.3.0): New features without breaking changes
- **Major releases** (1.2.3 → 2.0.0): Breaking changes, removals, or deprecations

## Single Source of Truth

```
Git Tag → setuptools_scm → Package Version → PyPI Version
```

All versions are derived from Git tags automatically. No manual version file editing required.

## Branch Strategy

This project follows a **two-branch workflow** for stable releases:

- **dev branch**: Development and testing
  - All new features and fixes are committed here
  - Pushes trigger TestPyPI publishing and full test suite
  - Used for pre-release validation

- **main branch**: Production releases only (PRIMARY BRANCH)
  - Only receives merges from dev
  - Version tags are created here
  - Tags trigger PyPI publishing and GitHub releases
  - Represents stable, released code
  - DEFAULT branch on GitHub

**Key Principle**: All version releases must originate from the main branch after merging from dev.

**Note**: The legacy `master` branch has been removed. All development now uses `main` as the primary branch (renamed in v1.1.0).

## Configuration

**pyproject.toml:**
```toml
[project]
dynamic = ["version"]  # Version is dynamic, not hardcoded

[tool.setuptools_scm]
version_scheme = "guess-next-dev"
local_scheme = "no-local-version"
fallback_version = "0.0.0"  # For uninitialized/non-git environments only
```

**How it works:**
- **With Git tag**: Uses tag as version (e.g., `v1.2.0` → `1.2.0`)
- **Between tags**: Adds dev suffix (e.g., `1.2.0.dev3+g7a8b9c0`)
- **No Git/tags**: Falls back to `0.0.0` (indicates uninitialized environment)

## Release Workflow

### Step 1: Development Phase (dev branch)

```bash
# Work on dev branch
git checkout dev

# Regular development commits
git add .
git commit -m "feat: Add new feature"
git push origin dev

# Triggers TestPyPI workflow:
# - Builds package
# - Publishes to TestPyPI
# - Runs full test suite (15 combinations)
# - Takes approximately 35 minutes

# Version during development: 1.1.0.dev1+g7100d29
```

### Step 2: Prepare Release (dev branch)

```bash
# 1. Update CHANGELOG.md with release notes
vim CHANGELOG.md

# 2. Move changes from [Unreleased] to new version section
## [1.2.0] - 2025-10-05

### Added
- New feature X
- Enhancement Y

### Fixed
- Bug Z

# 3. Commit the changelog
git add CHANGELOG.md
git commit -m "docs: Update CHANGELOG for v1.2.0 release"
git push origin dev

# Wait for TestPyPI workflow to complete and verify success
```

### Step 3: Merge to main branch

```bash
# Switch to main branch
git checkout main

# Merge dev into main
git merge dev

# Push to main (no workflow triggered yet)
git push origin main
```

### Step 4: Create Git Tag (main branch)

```bash
# Ensure you're on main branch
git checkout main

# Create annotated tag (REQUIRED for setuptools_scm)
git tag -a v1.2.0 -m "Release v1.2.0"

# Verify tag
git describe --tags
# Output: v1.2.0

# Push tag to remote
git push origin v1.2.0

# Triggers PyPI workflow:
# - Checks if commit was tested on TestPyPI
# - Builds package
# - Publishes to PyPI
# - Creates GitHub Release
# - Reuses TestPyPI tests (saves approximately 45 minutes)
# - Takes approximately 8 minutes (with test reuse)
```

### Step 5: Build and Publish (Alternative: Manual Publishing)

#### Option A: Manual Publishing

```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Check version in built package
tar -tzf dist/pyASDReader-1.2.0.tar.gz | grep PKG-INFO
tar -xzf dist/pyASDReader-1.2.0.tar.gz -O pyASDReader-1.2.0/PKG-INFO | grep Version

# Upload to TestPyPI (optional, for testing)
python -m twine upload --repository testpypi dist/*

# Upload to PyPI (production)
python -m twine upload dist/*
```

#### Option B: Automatic Publishing (GitHub Actions) - Recommended

The project uses a two-stage automated publishing workflow, which is covered in Steps 1-4 above.

**Workflow Summary**:
```bash
# Stage 1: Development Testing (TestPyPI)
git checkout dev
git push origin dev
# Wait for TestPyPI workflow to complete (approximately 35 min)

# Stage 2: Verify TestPyPI success at:
# https://github.com/YOUR_USERNAME/ASD_File_Reader/actions

# Stage 3: Merge to main and create release
git checkout main
git merge dev
git push origin main

# Stage 4: Push tag for production release
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
# PyPI workflow reuses TestPyPI tests (approximately 8 min)
```

**Total Time**: Approximately 30 minutes (vs approximately 50 min without test reuse)

See:
- `.github/workflows/publish-to-testpypi.yml` - Triggered by dev branch pushes
- `.github/workflows/publish-to-pypi.yml` - Triggered by version tags on main branch

## CI/CD Workflows

### TestPyPI Workflow (Dev Branch)

**Trigger**: Push to `dev` branch

**Purpose**: Automated testing before production release

**Process**:
1. Builds distribution packages
2. Publishes to TestPyPI
3. Runs comprehensive verification tests:
   - 3 operating systems: Ubuntu, Windows, macOS
   - 5 Python versions: 3.8, 3.9, 3.10, 3.11, 3.12
   - 15 total test combinations
4. Duration: Approximately 35 minutes

**Concurrency**: Automatically cancels outdated runs when new commits are pushed

### PyPI Workflow (Version Tags)

**Trigger**: Push tags matching `v*.*.*` (e.g., v1.2.0)

**Purpose**: Production release with intelligent test optimization

**Process**:
1. **Smart Test Reuse**:
   - Checks if commit was tested on TestPyPI (within 7 days)
   - Validates test completeness (15/15 jobs passed)
   - Skips verification if already tested

2. **Build & Publish**:
   - Builds distribution packages
   - Publishes to PyPI

3. **GitHub Release**:
   - Creates release with auto-generated notes
   - Extracts changelog for the version
   - Updates CITATION.cff
   - Attaches distribution packages

4. **Verification** (conditional):
   - **If tested on TestPyPI**: Skipped (saves approximately 45 min)
   - **If not tested**: Full verification (9 combinations)

5. **Summary**:
   - Displays test reuse status
   - Links to TestPyPI workflow (if reused)
   - Shows time saved

### Publishing Scenarios

#### Scenario 1: Normal Release (Recommended)
```bash
# 1. Push to dev branch and wait for TestPyPI
git checkout dev
git push origin dev              # Approximately 35 min (full tests)
# Wait for success...

# 2. Merge to main and create tag
git checkout main
git merge dev
git push origin main

# 3. Push tag on main branch
git push origin v1.2.0           # Approximately 8 min (tests reused)
# Total: Approximately 30 min
```

#### Scenario 2: Hotfix (Urgent Fix on main)
```bash
# 1. Create fix directly on main (bypass dev for urgent fixes)
git checkout main
git commit -m "fix: Critical security patch"
git push origin main

# 2. Push tag directly
git tag -a v1.2.1 -m "Hotfix: Critical security patch"
git push origin v1.2.1           # Approximately 23 min (full tests, no TestPyPI history)
# Safe fallback: always runs full verification

# 3. Back-merge to dev to keep branches in sync
git checkout dev
git merge main
git push origin dev
```

#### Scenario 3: Quick Release (Not Recommended)
```bash
# Push dev and tag simultaneously without merge
git push origin dev --tags       # Approximately 45 min (both run full tests in parallel)
# ⚠️ Warning: Tags not on main branch, breaks branch strategy
```

### Resource Optimization

**GitHub Actions Minutes**:
- TestPyPI per push: Approximately 35 minutes
- PyPI (normal release): Approximately 8 minutes (with test reuse)
- PyPI (hotfix): Approximately 35 minutes (full tests)

**Monthly Estimate** (20 dev pushes + 2 releases):
- TestPyPI: 20 × 35 = 700 min
- PyPI: 2 × 8 = 16 min
- **Total**: Approximately 716 min/month (approximately 36% of free tier 2000 min)

**Savings**: Approximately 40% compared to running full tests every time

## Version Verification

### Check Local Version

```bash
# Method 1: Using Python
python -c "from pyASDReader import __version__; print(__version__)"

# Method 2: Using setuptools_scm directly
python -m setuptools_scm

# Method 3: After installation
pip show pyASDReader | grep Version
```

### Check PyPI Version

```bash
# Latest version on PyPI
pip index versions pyASDReader

# Or visit
# https://pypi.org/project/pyASDReader/
```

### Check Git Tags

```bash
# List all tags
git tag -l

# Show latest tag
git describe --tags --abbrev=0

# Show detailed tag info
git show v1.2.0
```

## Semantic Versioning

Follow [Semantic Versioning 2.0.0](https://semver.org/):

```
v{MAJOR}.{MINOR}.{PATCH}

MAJOR: Incompatible API changes
MINOR: Backwards-compatible new features
PATCH: Backwards-compatible bug fixes
```

**Examples:**
- `v1.0.0` → `v1.0.1`: Bug fix release
- `v1.0.1` → `v1.1.0`: New feature added
- `v1.1.0` → `v2.0.0`: Breaking changes

## Troubleshooting

### Problem: Wrong version displayed

```bash
# Check what tag Git sees
git describe --tags

# If wrong tag is shown, check for duplicate tags
git tag -l

# Remove incorrect tag
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
```

### Problem: Version shows as fallback (0.0.0)

**Cause:** setuptools_scm not installed or not in Git repository

**Solution:**
```bash
# Install setuptools_scm
pip install setuptools_scm>=8

# Verify you're in a Git repo
git status

# Verify tags exist
git tag -l

# If tags exist, rebuild/reinstall the package
pip install -e .
```

### Problem: Duplicate tags on same commit

```bash
# Current status
git tag --points-at HEAD
# Output: v1.0.0
#         v1.1.0

# Delete the incorrect tag
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# Verify
git describe --tags
# Output: v1.1.0
```

### Problem: PyPI version doesn't match Git tag

**Cause:** Package was built before tag was created

**Solution:**
```bash
# 1. Clean old builds
rm -rf dist/ build/ *.egg-info

# 2. Verify current Git tag
git describe --tags

# 3. Rebuild
python -m build

# 4. Check built version
ls dist/
# Should show: pyASDReader-1.2.0.tar.gz

# 5. Re-upload (requires new version number on PyPI)
python -m twine upload dist/*
```

## Best Practices

1. **Follow the branch strategy**
   - **Development**: Always work on `dev` branch
   - **Releases**: Always tag on `main` branch after merging from `dev`
   - **Hotfixes**: Apply to `main`, then back-merge to `dev`
   - This keeps `main` stable and `dev` as the integration branch

2. **Always use annotated tags**: `git tag -a v1.2.0 -m "message"`
   - NOT `git tag v1.2.0` (lightweight tag)
   - Only create tags on `main` branch

3. **Never edit version files manually**
   - src/_version.py is auto-generated
   - pyproject.toml has `dynamic = ["version"]`

4. **Update CHANGELOG before tagging**
   - Users need to know what changed
   - Tag message can reference CHANGELOG
   - Update CHANGELOG on `dev` branch, then merge to `main`

5. **Test before releasing**
   - Run full test suite: `pytest tests/`
   - Test installation: `pip install -e .`
   - Verify version: `python -c "from pyASDReader import __version__; print(__version__)"`

6. **Use TestPyPI for testing**
   - Dev branch auto-publishes to TestPyPI
   - Always verify TestPyPI success before merging to main
   - TestPyPI tests are automatically reused by PyPI workflow
   - Manual test uploads: `bash scripts/publish.sh test`
   - Manual verification: `pip install -i https://test.pypi.org/simple/ pyASDReader`

7. **Follow the recommended release workflow**
   - Push to dev first, wait for TestPyPI to complete
   - Verify tests passed in GitHub Actions
   - Merge dev to main
   - Then push tag from main for production release
   - This ensures maximum test coverage with minimal Actions minutes

8. **Understand workflow behavior**
   - TestPyPI: Full tests on every dev push
   - PyPI: Smart test reuse (7-day window)
   - Hotfix tags: Auto-fallback to full testing
   - Concurrent dev pushes: Auto-cancel outdated runs

9. **One tag per release**
   - Don't create multiple tags on same commit
   - Don't move tags after pushing
   - Verify tag is on main: `git branch --contains <tag>`

10. **Keep branches in sync**
    - After hotfixes on main, always back-merge to dev
    - Prevents divergence between branches
    - Use `git merge main` on dev branch after hotfix releases

## Automated Release Script

For maintainers, use the automated release script for streamlined releases:

```bash
# Automated release (recommended)
bash scripts/release.sh patch  # 1.2.3 -> 1.2.4
bash scripts/release.sh minor  # 1.2.3 -> 1.3.0
bash scripts/release.sh major  # 1.2.3 -> 2.0.0
```

The script handles:
- Pre-flight checks (branch, working directory, tests)
- CHANGELOG.md updates
- Version tagging
- Branch merging (dev -> main)
- Tag pushing (triggers CI/CD)

**Total time**: ~2 minutes of manual work + 5-10 minutes CI/CD (with test reuse)

**Note**: Times vary based on test execution and PyPI availability. Expect longer durations (30-40 min) without test reuse.

See `scripts/release.sh` for details.

## Quick Reference

```bash
# Development workflow (dev branch)
git checkout dev
git commit -m "feat: New feature"
git push origin dev
# Triggers TestPyPI publish + full tests (approximately 35 min)

# Release workflow (recommended)
# Step 1: Update CHANGELOG on dev
git checkout dev
vim CHANGELOG.md
git commit -m "docs: Update CHANGELOG for v1.2.0"
git push origin dev
# Wait for TestPyPI success

# Step 2: Merge to main
git checkout main
git merge dev
git push origin main

# Step 3: Create and push tag on main
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
# PyPI publish + test reuse (approximately 8 min)

# Hotfix workflow (emergency on main)
git checkout main
git commit -m "fix: Critical bug"
git push origin main
git tag -a v1.2.1 -m "Hotfix: Critical bug"
git push origin v1.2.1
# PyPI publish + full tests (approximately 23 min)
# Don't forget to back-merge to dev:
git checkout dev
git merge main
git push origin dev

# Manual publishing (if needed)
python -m build
python -m twine upload dist/*

# Verification commands
git describe --tags
git branch --contains $(git describe --tags)  # Check which branch has the tag
python -c "from pyASDReader import __version__; print(__version__)"
pip index versions pyASDReader

# Check workflow status
# https://github.com/YOUR_USERNAME/ASD_File_Reader/actions
```

## Emergency Procedures

For critical issues requiring version rollback:

See [VERSION_ROLLBACK.md](VERSION_ROLLBACK.md) for:
- Quick rollback procedure (10-15 minutes)
- Detailed rollback steps
- Post-rollback actions
- Prevention strategies

**When to rollback**:
- Critical bugs affecting core functionality
- Security vulnerabilities
- Data corruption issues
- Major compatibility problems

## Additional Documentation

- **[CONTRIBUTING.md](https://github.com/KaiTastic/pyASDReader/blob/main/CONTRIBUTING.md)**: Contribution guidelines
- **[VERSION_ROLLBACK.md](VERSION_ROLLBACK.md)**: Emergency rollback procedures
- **[GITHUB_ENVIRONMENT_SETUP.md](GITHUB_ENVIRONMENT_SETUP.md)**: Production deployment protection

## Automation and Tools

### Pre-commit Hooks
- Version consistency check
- CHANGELOG format validation
- Commit message format validation

Setup: `pre-commit install && pre-commit install --hook-type commit-msg`

### Dependabot
- Automated dependency updates
- Weekly checks (Mondays 09:00 UTC)
- Grouped updates by category

Config: `.github/dependabot.yml`

### CI/CD Workflows
- **python-package.yml**: Full testing (15 combinations)
- **publish-to-testpypi.yml**: Dev branch publishing (9 combinations)
- **publish-to-pypi.yml**: Production releases (intelligent test reuse)

## Troubleshooting

### Trusted Publishing Issues

If you encounter "Trusted publishing exchange failure" errors:

1. **Quick Diagnostic**:
   ```bash
   bash scripts/diagnose_trusted_publishing.sh
   ```

2. **Common Causes**:
   - PyPI Trusted Publisher not configured
   - Configuration mismatch (Owner/Repository/Workflow/Environment)
   - GitHub Environment not created
   - Missing `id-token: write` permission

3. **Detailed Guides**:
   - [Trusted Publishing Setup](TRUSTED_PUBLISHING_SETUP.md)
   - [Troubleshooting Guide](TROUBLESHOOTING_TRUSTED_PUBLISHING.md)
   - [API Token Fallback](FALLBACK_API_TOKEN_SETUP.md)

4. **Debug Workflow**:
   ```bash
   gh workflow run debug-trusted-publishing.yml
   gh run watch
   ```

### Release Script Issues

If `release.sh` fails:

1. **Check prerequisites**:
   ```bash
   python3 --version  # Python 3 required
   git status         # Clean working directory
   git branch         # On dev branch
   ```

2. **Validation failures**:
   ```bash
   # Run validation manually
   python3 scripts/validate_release.py --new-version 1.2.4 --version-type patch
   ```

3. **Rollback if needed**:
   ```bash
   bash scripts/release.sh --rollback
   ```

### Workflow Failures

If GitHub Actions workflows fail:

1. **Check recent runs**:
   ```bash
   gh run list --workflow=publish-to-pypi.yml --limit=5
   gh run view --log-failed
   ```

2. **Tag verification failed**:
   - Ensure tag is on `main` branch
   - Delete and recreate tag on correct branch

3. **Test reuse issues**:
   - TestPyPI tests expire after 7 days
   - Force new tests by pushing to dev branch first

## References

- [setuptools_scm documentation](https://setuptools-scm.readthedocs.io/)
- [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
- [PEP 440 - Version Identification](https://peps.python.org/pep-0440/)
- [Git Tagging Documentation](https://git-scm.com/book/en/v2/Git-Basics-Tagging)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Trusted Publishing Documentation](https://docs.pypi.org/trusted-publishers/)

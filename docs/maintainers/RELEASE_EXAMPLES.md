# Release Examples and Scenarios

This document provides detailed examples for various release scenarios in pyASDReader.

## Table of Contents

- [Normal Release Flow](#normal-release-flow)
- [Hotfix Release](#hotfix-release)
- [First Time Release](#first-time-release)
- [Pre-release/Beta](#pre-releasebeta)
- [Rolling Back a Release](#rolling-back-a-release)
- [Manual Release](#manual-release)

## Normal Release Flow

### Scenario: Minor Version Release (1.2.3 → 1.3.0)

**Timeline**: ~45 minutes total

#### Step 1: Development on dev branch

```bash
# Ensure you're on dev branch
git checkout dev
git pull origin dev

# Make your changes
git add .
git commit -m "feat: Add new spectral analysis feature"
git push origin dev

# This triggers TestPyPI workflow (~35 min)
# Wait for it to complete: https://github.com/KaiTastic/pyASDReader/actions
```

#### Step 2: Update CHANGELOG

```bash
# Edit CHANGELOG.md
vim CHANGELOG.md
```

Add your changes to the [Unreleased] section:
```markdown
## [Unreleased]

### Added
- New spectral analysis feature for derivative calculations
- Support for custom wavelength ranges

### Fixed
- Corrected GPS coordinate parsing for negative longitudes
```

```bash
# Commit CHANGELOG
git add CHANGELOG.md
git commit -m "docs: Update CHANGELOG for v1.3.0"
git push origin dev
```

#### Step 3: Release using automated script

```bash
# Run release script (handles everything automatically)
bash scripts/release.sh minor

# The script will:
# 1. Verify you're on dev branch
# 2. Calculate new version (1.2.3 → 1.3.0)
# 3. Move CHANGELOG [Unreleased] to [1.3.0]
# 4. Commit changes
# 5. Merge dev to main
# 6. Create tag v1.3.0
# 7. Push to remote (triggers PyPI workflow ~8 min with test reuse)
# 8. Back-merge to dev
```

#### Step 4: Verify release

```bash
# Check GitHub Actions
# https://github.com/KaiTastic/pyASDReader/actions

# Verify PyPI (wait 2-5 minutes)
pip index versions pyASDReader

# Test installation
pip install --upgrade pyASDReader
python -c "from pyASDReader import __version__; print(__version__)"
```

**Total Time**: 35 min (TestPyPI) + 8 min (PyPI) + 5 min (manual steps) = **~48 minutes**

---

## Hotfix Release

### Scenario: Critical Bug Fix (1.3.0 → 1.3.1)

**Timeline**: ~40 minutes (urgent path)

#### Step 1: Fix on main branch

```bash
# Critical bugs can be fixed directly on main
git checkout main
git pull origin main

# Make the fix
vim src/asd_file_reader.py

# Commit with fix: prefix
git add .
git commit -m "fix: Correct null pointer in wavelength calculation

This fixes a critical bug that causes crashes when processing
files without calibration data."
git push origin main
```

#### Step 2: Create hotfix release

```bash
# Create and push tag directly
git tag -a v1.3.1 -m "Hotfix v1.3.1: Fix null pointer crash

Critical fix for wavelength calculation crash.
Affects all users processing files without calibration data."

git push origin v1.3.1

# This triggers PyPI workflow
# Since commit wasn't tested on TestPyPI, runs full verification (~35 min)
```

#### Step 3: Back-merge to dev

```bash
# IMPORTANT: Sync dev branch with hotfix
git checkout dev
git merge main
git push origin dev
```

#### Step 4: Update CHANGELOG (post-release)

```bash
# Update CHANGELOG to document the hotfix
vim CHANGELOG.md
```

Add:
```markdown
## [1.3.1] - 2025-10-08

### Fixed
- Critical: Fixed null pointer crash in wavelength calculation
- Affects users processing files without calibration data
```

```bash
git add CHANGELOG.md
git commit -m "docs: Document v1.3.1 hotfix in CHANGELOG"
git push origin dev
```

**Total Time**: 35 min (PyPI full tests) + 5 min (manual) = **~40 minutes**

---

## First Time Release

### Scenario: Initial Public Release (0.0.0 → 1.0.0)

#### Prerequisites

1. **Set up PyPI accounts**:
   - Create account at https://pypi.org/
   - Create account at https://test.pypi.org/
   - Generate API tokens for both

2. **Configure GitHub secrets**:
   ```
   Settings → Secrets and variables → Actions → New repository secret

   Name: PYPI_API_TOKEN
   Value: pypi-...

   Name: TEST_PYPI_API_TOKEN
   Value: pypi-...
   ```

3. **Register project name** (if needed):
   ```bash
   # Upload to TestPyPI first to claim name
   python -m build
   python -m twine upload --repository testpypi dist/*
   ```

#### Release Process

```bash
# 1. Ensure code is ready
git checkout main
pytest tests/  # All tests must pass

# 2. Prepare CHANGELOG
vim CHANGELOG.md
```

Add initial release notes:
```markdown
## [1.0.0] - 2025-10-08

### Added
- Initial public release
- Support for all ASD file versions (v1-v8)
- Comprehensive spectral data extraction
- Full test suite with 100+ tests
- Documentation and examples
```

```bash
# 3. Commit and tag
git add CHANGELOG.md
git commit -m "chore: Prepare v1.0.0 release"
git push origin main

git tag -a v1.0.0 -m "Release v1.0.0 - Initial public release"
git push origin v1.0.0

# 4. Monitor workflow
# https://github.com/KaiTastic/pyASDReader/actions

# 5. Verify on PyPI (after ~35 min)
pip install pyASDReader
```

---

## Pre-release/Beta

### Scenario: Beta Testing (1.3.0 → 1.4.0-beta.1)

**Note**: setuptools_scm handles dev versions automatically, but for explicit pre-releases, use manual tagging.

#### Option 1: Using setuptools_scm dev versions

```bash
# Simply develop on dev branch
git checkout dev
# Make changes...
git push origin dev

# Version automatically becomes: 1.3.0.dev1+g<commit-hash>
# Publish to TestPyPI for beta testing
```

#### Option 2: Explicit pre-release tags

```bash
# Create pre-release tag
git checkout main
git merge dev
git tag -a v1.4.0b1 -m "Beta release 1.4.0-beta.1"
git push origin v1.4.0b1

# Upload to TestPyPI only (modify workflow or manual upload)
python -m build
python -m twine upload --repository testpypi dist/*
```

#### Beta Testing Instructions for Users

```bash
# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            pyASDReader

# Or specific dev version
pip install pyASDReader==1.3.0.dev1
```

---

## Rolling Back a Release

### Scenario: Critical Issue in v1.3.0, Need to Revert

See [VERSION_ROLLBACK](VERSION_ROLLBACK.md) for complete rollback procedures.

#### Quick Rollback Summary

```bash
# 1. Yank the problematic version on PyPI (preferred)
# Go to: https://pypi.org/manage/project/pyASDReader/releases/
# Select v1.3.0 → Options → "Yank release"
# Reason: "Critical bug causing data corruption"

# 2. Create hotfix release
git checkout main
git checkout v1.2.3  # Last good version
# Apply critical fix
git cherry-pick <fix-commit>

# 3. Release as v1.3.1
git tag -a v1.3.1 -m "Hotfix: Revert breaking changes from v1.3.0"
git push origin v1.3.1
```

**Note**: Yanked versions remain visible but pip won't install them by default.

---

## Manual Release

### Scenario: Workflow Issues, Need Manual Release

#### When to Use Manual Release
- GitHub Actions down
- Workflow errors
- Need to test before automation
- Custom build requirements

#### Process

```bash
# 1. Clean and build
rm -rf dist/ build/ *.egg-info
python -m build

# 2. Check distribution
python -m twine check dist/*
ls -lh dist/
# Should see:
#   pyASDReader-1.3.0-py3-none-any.whl
#   pyASDReader-1.3.0.tar.gz

# 3. Upload to TestPyPI (testing)
python -m twine upload --repository testpypi dist/*

# 4. Test installation
python -m venv test_env
source test_env/bin/activate  # or `test_env\Scripts\activate` on Windows
pip install --index-url https://test.pypi.org/simple/ \
            --extra-index-url https://pypi.org/simple/ \
            pyASDReader

# Run tests
python -c "from pyASDReader import ASDFile; print('OK')"
deactivate
rm -rf test_env

# 5. Upload to PyPI (production)
python -m twine upload dist/*

# 6. Create GitHub Release manually
# Go to: https://github.com/KaiTastic/pyASDReader/releases/new
# Tag: v1.3.0
# Title: Release v1.3.0
# Body: Copy from CHANGELOG.md
# Attach files: dist/*
```

---

## Advanced Scenarios

### Releasing Multiple Versions

**Scenario**: Need to support v1.x and v2.x simultaneously

```bash
# Maintain separate branches
git checkout -b v1-maintenance
git push origin v1-maintenance

# Release 1.x patch
git checkout v1-maintenance
# Make changes...
git tag v1.3.2
git push origin v1.3.2

# Release 2.x feature
git checkout main
# Make changes...
git tag v2.0.0
git push origin v2.0.0
```

### Fixing a Released Version

**Scenario**: Need to update package metadata without code changes

```bash
# Update metadata
vim pyproject.toml  # Fix description, URLs, etc.
vim README.md       # Fix documentation

# Bump patch version
git add pyproject.toml README.md
git commit -m "docs: Update package metadata"
git tag v1.3.1  # Must use new version
git push origin v1.3.1
```

### Emergency Release

**Scenario**: Critical security patch, need fastest possible release

```bash
# 1. Fix immediately on main
git checkout main
# Apply fix...
git commit -m "security: Fix CVE-2025-XXXXX"

# 2. Tag and push together
git tag -a v1.3.1 -m "Security fix: CVE-2025-XXXXX"
git push origin main v1.3.1

# 3. Notify users
# Post to GitHub Discussions/Issues
# Update security advisory

# 4. Clean up later
# Update CHANGELOG
# Back-merge to dev
```

**Timeline**: Can be done in ~10 minutes + 35 min CI/CD

---

## Troubleshooting

### Release Script Fails

**Error**: "You have uncommitted changes"

```bash
# Check status
git status

# Stash or commit changes
git stash  # or git commit
bash scripts/release.sh minor
git stash pop
```

**Error**: "Tests failed"

```bash
# Fix tests first
pytest tests/ -v

# Or skip tests (not recommended)
# Edit release.sh temporarily or fix the issue
```

### Tag Already Exists

**Error**: "tag 'v1.3.0' already exists"

```bash
# Delete local tag
git tag -d v1.3.0

# Delete remote tag
git push origin :refs/tags/v1.3.0

# Recreate
git tag -a v1.3.0 -m "Release v1.3.0"
git push origin v1.3.0
```

### PyPI Upload Fails

**Error**: "File already exists"

**Cause**: Version already uploaded to PyPI (cannot replace)

**Solution**:
```bash
# Must use new version number
git tag -d v1.3.0
git push origin :refs/tags/v1.3.0

# Use next patch version
git tag -a v1.3.1 -m "Release v1.3.1"
git push origin v1.3.1
```

---

## Best Practices Summary

1. ✅ **Always develop on dev branch**
2. ✅ **Update CHANGELOG before releasing**
3. ✅ **Wait for TestPyPI tests to pass**
4. ✅ **Use automated release script**
5. ✅ **Tag on main branch only**
6. ✅ **Back-merge hotfixes to dev**
7. ✅ **Monitor CI/CD workflows**
8. ✅ **Test installations after release**
9. ✅ **Document all releases in CHANGELOG**
10. ✅ **Communicate breaking changes clearly**

---

## Quick Reference

```bash
# Normal release (automated)
bash scripts/release.sh patch   # 1.2.3 → 1.2.4
bash scripts/release.sh minor   # 1.2.3 → 1.3.0
bash scripts/release.sh major   # 1.2.3 → 2.0.0

# Hotfix (manual)
git checkout main
# fix...
git commit -m "fix: Critical bug"
git tag -a v1.3.1 -m "Hotfix"
git push origin main v1.3.1
git checkout dev && git merge main && git push

# Check release status
git describe --tags                    # Current version
pip index versions pyASDReader        # PyPI versions
# https://github.com/KaiTastic/pyASDReader/actions  # Workflows
```

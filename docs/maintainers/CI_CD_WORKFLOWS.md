# CI/CD Workflows Documentation

This document provides detailed information about the GitHub Actions workflows used for testing, building, and publishing pyASDReader.

## Overview

pyASDReader uses four main workflows:

1. **python-package.yml** - Full testing on pull requests and pushes
2. **publish-to-testpypi.yml** - Development testing and TestPyPI publishing
3. **publish-to-pypi.yml** - Production releases with intelligent test reuse
4. **sync-branches.yml** - Automatic branch synchronization after releases

## Workflow Details

### 1. Python Package Testing (`python-package.yml`)

**Trigger**: Push to any branch, Pull requests

**Purpose**: Comprehensive testing across all supported environments

**Test Matrix**:
- 3 Operating Systems: Ubuntu, Windows, macOS
- 5 Python Versions: 3.8, 3.9, 3.10, 3.11, 3.12
- **Total**: 15 test combinations

**Duration**: ~15-20 minutes

**Steps**:
1. Check out code with full git history (for setuptools_scm)
2. Set up Python environment with pip caching
3. Install dependencies: `pip install -e ".[dev]"`
4. Run tests with pytest and coverage
5. Upload coverage to Codecov

**Features**:
- Fail-fast disabled (runs all combinations even if one fails)
- Codecov integration for coverage tracking
- Per-platform coverage flags

### 2. TestPyPI Publishing (`publish-to-testpypi.yml`)

**Trigger**: Push to `dev` branch (filtered paths)

**Purpose**: Pre-release validation and TestPyPI publishing

**Concurrency**: Cancels outdated runs automatically

**Test Matrix**:
- 3 Operating Systems: Ubuntu, Windows, macOS
- 5 Python Versions: 3.8, 3.9, 3.10, 3.11, 3.12
- **Total**: 15 verification jobs

**Duration**: ~35 minutes

**Steps**:
1. **Build** (ubuntu-latest, Python 3.11):
   - Checkout with full git history
   - Install build tools (build, twine, setuptools-scm)
   - Build distribution packages
   - Check packages with twine
   - Upload artifacts (7-day retention)

2. **Publish to TestPyPI**:
   - Download build artifacts
   - Publish using PyPA action with API token
   - Skip if version already exists

3. **Verify Installation** (15 jobs):
   - Wait 120 seconds for TestPyPI to update
   - Install from TestPyPI
   - Retry once if failed (wait additional 60s)
   - Verify imports and package metadata

**Path Filters**:
Triggers on changes to:
- `src/**`
- `pyproject.toml`
- `CHANGELOG.md`
- `README.md`
- Workflow file itself

### 3. PyPI Production Publishing (`publish-to-pypi.yml`)

**Trigger**: Tags matching `v*.*.*` (e.g., v1.2.0)

**Purpose**: Production releases with intelligent test optimization

**Duration**:
- With test reuse: ~8 minutes (skips verification)
- Without test reuse: ~35 minutes (full verification)

**Jobs**:

#### Job 1: Check Previous Tests
**Purpose**: Determine if commit was already tested on TestPyPI

**Logic**:
```bash
# Query TestPyPI workflow runs from last 7 days
# Check if commit SHA matches
# Verify 15/15 verification jobs passed
# Output: tested=true/false, run_id, url
```

#### Job 2: Build
Same as TestPyPI workflow

#### Job 3: Publish to PyPI
- Downloads build artifacts
- **Requires manual approval** via GitHub Environment (`pypi-production`)
- Publishes using PyPA action with OIDC trusted publishing

#### Job 4: Create GitHub Release
**Steps**:
1. Extract version from tag
2. Update CITATION.cff (if exists)
3. Extract changelog for this version
4. Create release with:
   - Distribution packages
   - CITATION.cff
   - Auto-generated notes
   - Extracted changelog

#### Job 5: Verify Installation (Conditional)
**Condition**: Only runs if NOT tested on TestPyPI

Same as TestPyPI verification

#### Job 6: Verification Summary
**Purpose**: Display test reuse status

**Outputs**:
- Test reuse status (REUSED/COMPLETED/SKIPPED)
- Link to TestPyPI run (if reused)
- Time saved estimate

## Test Reuse Mechanism

### How It Works

1. **On Tag Push**:
   - Check if commit SHA was tested on TestPyPI within 7 days
   - Verify 15/15 verification jobs passed
   - If yes: Skip verification, use TestPyPI results
   - If no: Run full 15-job verification

2. **Benefits**:
   - Saves ~60 minutes of GitHub Actions time per release
   - Ensures same tests used for TestPyPI and PyPI
   - Reduces redundant testing

3. **Safety**:
   - Only reuses tests less than 7 days old
   - Requires 100% success (15/15 jobs)
   - Falls back to full testing if uncertain

### Example Scenarios

#### Scenario 1: Normal Release (Recommended)
```bash
# Day 1: Push to dev
git push origin dev
# Triggers TestPyPI → 35 min (15 verification jobs)

# Day 2: Merge and tag
git checkout main && git merge dev
git tag v1.2.0 && git push origin v1.2.0
# Triggers PyPI → 8 min (tests reused)
# Total: 43 min
```

#### Scenario 2: Hotfix (Urgent)
```bash
# Direct fix on main
git checkout main
git commit -m "fix: Critical bug"
git tag v1.2.1 && git push origin main v1.2.1
# Triggers PyPI → 35 min (full verification, no TestPyPI history)

# Back-merge to dev
git checkout dev && git merge main && git push
```

#### Scenario 3: Old Commit
```bash
# Tag a 20-day-old commit
git tag v1.2.0 <old-commit-sha>
git push origin v1.2.0
# Triggers PyPI → 35 min (TestPyPI tests too old, expired)
```

## Resource Usage

### GitHub Actions Minutes

**Monthly Estimate** (assuming 20 dev pushes, 2 releases):
- TestPyPI: 20 × 35 min = 700 min
- PyPI: 2 × 8 min = 16 min (with reuse)
- **Total**: ~716 min/month (36% of free tier 2000 min)

**Without Test Reuse**:
- TestPyPI: 20 × 35 min = 700 min
- PyPI: 2 × 35 min = 70 min
- **Total**: ~770 min/month
- **Savings**: ~54 min/month (~7%)

**With More Frequent Releases** (10/month):
- TestPyPI: 20 × 35 min = 700 min
- PyPI: 10 × 8 min = 80 min (with reuse)
- **Total**: ~780 min/month
- **Savings**: ~270 min/month (~26%)

## Configuration

### Trusted Publishing (OIDC) - Current Method

This project uses PyPI's **Trusted Publishing** feature for secure, passwordless deployment:

**Setup on PyPI**:
1. Go to: https://pypi.org/manage/project/pyASDReader/settings/publishing/
2. Add GitHub Actions publisher with:
   - **Repository**: KaiTastic/pyASDReader
   - **Workflow**: publish-to-pypi.yml
   - **Environment**: pypi-production (optional, see below)

**Setup on TestPyPI**:
1. Go to: https://test.pypi.org/manage/project/pyASDReader/settings/publishing/
2. Add GitHub Actions publisher with:
   - **Repository**: KaiTastic/pyASDReader
   - **Workflow**: publish-to-testpypi.yml
   - **Environment**: (leave empty for dev branch)

**Workflow Configuration**:
The workflows already include:
```yaml
permissions:
  id-token: write  # Enable OIDC token for trusted publishing
```

**Benefits**:
- ✅ No API tokens to manage or rotate
- ✅ Automatic authentication via OpenID Connect
- ✅ More secure (tokens can't be leaked)
- ✅ Scoped per-workflow permissions

**Migration Note**: If you previously used API tokens (`PYPI_API_TOKEN`, `TEST_PYPI_API_TOKEN`), you can safely delete them from GitHub Secrets after confirming trusted publishing works

### GitHub Environment (ENABLED)

**Status**: ✅ Environment protection is now enabled for production releases

This provides an additional safety gate requiring manual approval before publishing to PyPI.

**Setup Required** (one-time configuration):

1. Go to: Settings → Environments → New environment
2. Name: `pypi-production`
3. Configure protection rules:
   - **Required reviewers**: Add at least 1 maintainer
   - **Wait timer**: 5 minutes (optional, for last-minute checks)
   - **Deployment branches**: Only `main` (prevents accidental releases from other branches)

4. The workflow is already configured to use this environment:
   ```yaml
   environment:
     name: pypi-production
     url: https://pypi.org/project/pyASDReader/
   ```

**Benefits**:
- Prevents accidental production releases
- Allows for last-minute review before PyPI publication
- Provides an audit trail of who approved each release
- Can be overridden by repository administrators in emergencies

## Monitoring and Debugging

### View Workflow Runs

- All runs: https://github.com/KaiTastic/pyASDReader/actions
- Specific workflow: Click workflow name in left sidebar

### Common Issues

#### 1. TestPyPI Upload Fails: "File already exists"
**Cause**: Version already published to TestPyPI

**Solution**: Expected behavior, `skip-existing: true` prevents error

#### 2. PyPI Upload Fails: "File already exists"
**Cause**: Version already published to PyPI

**Solution**: Cannot republish to PyPI, must use new version number

#### 3. Verification Fails: "Module not found"
**Cause**: Package not yet available on PyPI/TestPyPI

**Solution**: Retry logic waits 120s + 60s, usually resolves automatically

#### 4. Test Reuse Not Working
**Causes**:
- Commit not pushed to dev first
- TestPyPI tests failed or incomplete
- Tests older than 7 days

**Solution**: Check verification summary for details

#### 5. Tag Triggers Wrong Branch
**Cause**: Tag created on wrong branch

**Solution**: Delete tag, checkout main, recreate:
```bash
git tag -d v1.2.0
git push origin :refs/tags/v1.2.0
git checkout main
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0
```

## Best Practices

1. **Always Test on TestPyPI First**
   - Push to dev branch before releasing
   - Wait for TestPyPI workflow to complete
   - Verify success before merging to main

2. **Tag on Main Branch Only**
   - Ensures clean release history
   - Enables proper test reuse
   - Maintains branch strategy

3. **Monitor Workflow Runs**
   - Check for failures immediately
   - Review verification summary
   - Watch for deprecation warnings

4. **Use Semantic Versioning**
   - Tags determine version numbers
   - Follow MAJOR.MINOR.PATCH format
   - Update CHANGELOG accordingly

5. **Keep Workflows Updated**
   - Review GitHub Actions updates
   - Update action versions annually
   - Test changes on dev branch first

### 4. Branch Synchronization (`sync-branches.yml`)

**Trigger**: Push to `main` branch (excluding merges from dev)

**Purpose**: Automatically keep dev branch in sync with main after hotfixes or releases

**Behavior**:
1. **Detection**: Checks if push to main originated from dev merge
   - If yes: Skip (no action needed)
   - If no: Proceed with sync attempt

2. **Automatic Sync**:
   - Attempts to merge main into dev automatically
   - If successful: Pushes merged changes to dev
   - If conflicts: Creates GitHub Issue for manual resolution

3. **Failure Handling**:
   - Creates detailed issue with conflict information
   - Provides step-by-step resolution instructions
   - Lists conflicting files
   - Auto-closes issue when branches are synced

**Key Features**:
- **Prevents branch divergence**: Ensures dev has all hotfix changes
- **Conflict resolution**: Clear instructions when automatic merge fails
- **Issue tracking**: GitHub Issues for manual intervention
- **Concurrency control**: Prevents overlapping sync operations

**Workflow Steps**:
```yaml
1. Checkout repository with full history
2. Configure git for bot commits
3. Check if push was from dev merge (skip if true)
4. Check branch divergence
5. Attempt automatic merge:
   - Success → Push to dev automatically
   - Failure → Create issue with instructions
6. Close existing sync issues if branches now in sync
```

**Example Scenarios**:

**Scenario A: Hotfix on main**
```bash
# A critical bug fix is pushed directly to main
git checkout main
git commit -m "hotfix: Critical security patch"
git push origin main

# Workflow automatically:
# 1. Detects this wasn't from dev
# 2. Merges main → dev (if no conflicts)
# 3. Pushes to dev
# Result: dev branch updated automatically
```

**Scenario B: Conflict detected**
```bash
# Workflow detects conflicts during auto-merge
# Creates GitHub Issue:
# - Title: "⚠️ Manual Branch Sync Required"
# - Lists conflicting files
# - Provides resolution commands
# - Adds labels: 'sync-required', 'urgent'
```

**Issue Format**:
- **Commits ahead**: Number of commits main is ahead of dev
- **Conflicting files**: Specific files with conflicts
- **Resolution steps**: Copy-paste commands
- **Why important**: Explanation of sync necessity

**Benefits**:
- Reduces manual branch maintenance
- Prevents forgotten back-merges
- Immediate visibility when manual action needed
- Maintains GitFlow branch strategy

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyPA GitHub Actions](https://github.com/pypa/gh-action-pypi-publish)
- [setuptools_scm](https://setuptools-scm.readthedocs.io/)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [Codecov Documentation](https://docs.codecov.com/)

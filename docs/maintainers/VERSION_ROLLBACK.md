# Version Rollback and Emergency Procedures

Quick guide for rolling back problematic releases.

## When to Rollback

**Rollback for**:
- Critical bugs breaking core functionality
- Security vulnerabilities
- Data corruption issues
- Major compatibility problems
- Installation failures preventing user access

**DON'T rollback for**:
- Minor bugs → Fix with patch release
- Documentation errors → Update docs
- Performance issues → Optimize in next release

## Quick Rollback (10-15 minutes)

### Option A: Yank Release (Recommended)

PyPI's yank feature is preferred over deletion:

```bash
# 1. Yank the bad version on PyPI
# Go to: https://pypi.org/manage/project/pyASDReader/releases/
# Click problematic version → "Options" → "Yank release"
# Reason: "Critical bug: <description>"

# 2. Release hotfix immediately
git checkout main
# Apply fix
git commit -m "fix: Critical bug from v1.2.3"
git tag -a v1.2.4 -m "Hotfix: Fixes critical issue in v1.2.3"
git push origin main v1.2.4

# 3. Update CHANGELOG
# Document the issue and fix in v1.2.4

# 4. Back-merge to dev
git checkout dev && git merge main && git push origin dev
```

**Why yank?**
- Version remains visible but pip won't install it
- Preserves version history
- Users see warning about yanked version
- Can still install with `pip install pyASDReader==1.2.3 --force-reinstall`

### Option B: Republish Last Good Version

If yank isn't sufficient (extremely rare):

```bash
# 1. Delete bad version from PyPI (IRREVERSIBLE)
# Go to: https://pypi.org/manage/project/pyASDReader/releases/
# Click version → "Options" → "Delete"

# 2. Checkout last good version
git checkout v1.2.2  # Last known good

# 3. Create new version tag (can't reuse numbers)
git tag -a v1.2.4 -m "Rollback: Restores v1.2.2 code

Critical issues in v1.2.3:
- [List issues]

Version 1.2.3 has been removed from PyPI."

# 4. Push tag (triggers release)
git push origin v1.2.4
```

**Note**: Version numbers must increase, can't republish v1.2.2.

## Detailed Rollback Steps

### Step 1: Assess and Document

```bash
# Identify problematic version
pip index versions pyASDReader

# Find last good version
git tag -l --sort=-version:refname | head -5
git show v1.2.2  # Verify it's stable

# Create GitHub issue
# Title: "Critical: Version 1.2.3 has breaking bug"
# Labels: critical, bug
# Description: Impact, reproduction steps, affected users
```

### Step 2: Immediate User Communication

Post announcement immediately:

```markdown
## Critical: Version 1.2.3 Issue

**Action Required**: Do NOT use v1.2.3

**Issue**: [Brief description]

**Affected**: [Who is affected]

**Status**:
- ❌ v1.2.3 has been yanked from PyPI
- ✅ v1.2.4 hotfix in progress (ETA: X hours)
- ✅ v1.2.2 is stable, use as workaround

**Workaround**:
```bash
pip install pyASDReader==1.2.2
```

**Update**: [Timestamp] - Status updates posted here
```

Post to:
- GitHub Discussions
- GitHub Issues
- README.md (temporary warning banner)

### Step 3: Execute Rollback

Choose appropriate method from Quick Rollback section above.

### Step 4: Verify

```bash
# Test installation
python -m venv test_env
source test_env/bin/activate
pip install pyASDReader

# Verify correct version
python -c "from pyASDReader import __version__; print(__version__)"
# Should show 1.2.4 or 1.2.2

# Run smoke tests
python -c "from pyASDReader import ASDFile; print('OK')"

# Clean up
deactivate && rm -rf test_env
```

## Post-Rollback Actions

### Immediate (24 hours)

1. **Update documentation**
   ```bash
   # Update CHANGELOG.md
   vim CHANGELOG.md
   ```

   Add:
   ```markdown
   ## [1.2.4] - YYYY-MM-DD

   ### Fixed
   - **CRITICAL**: Fixed [issue] from v1.2.3
   - v1.2.3 has been yanked from PyPI

   ### Note
   If you installed v1.2.3, upgrade immediately:
   ```bash
   pip install --upgrade pyASDReader
   ```
   ```

2. **Monitor and support users**
   - Watch GitHub issues for related reports
   - Respond to user questions quickly
   - Track who might be affected

3. **Root cause analysis**
   - Why did the bug slip through?
   - Were tests insufficient?
   - Was review process adequate?

### Short-term (1 week)

1. **Improve testing**
   ```bash
   # Add regression test
   vim tests/test_regression_v123.py
   ```

   Ensure bug can't reoccur.

2. **Update CI/CD if needed**
   - Add missing test coverage
   - Improve validation checks
   - Enhance review process

3. **Document lessons learned**
   ```bash
   # Add to project documentation
   vim docs/POST_MORTEM_v123.md
   ```

## Prevention Strategies

### Before Releasing

1. **Always test on TestPyPI first**
   ```bash
   # Push to dev triggers TestPyPI
   git push origin dev
   # Wait for success, then release
   ```

2. **Use release script validation**
   ```bash
   bash scripts/release.sh minor --dry-run
   python scripts/validate_release.py --run-tests
   ```

3. **Manual testing checklist**
   - [ ] Install from TestPyPI in clean environment
   - [ ] Run full test suite locally
   - [ ] Test basic import and functionality
   - [ ] Check all dependencies install correctly
   - [ ] Verify on multiple Python versions

4. **Code review**
   - At least one reviewer for significant changes
   - Focus on breaking changes
   - Check deprecation warnings

### After Releasing

1. **Monitor for 48 hours**
   - Watch GitHub issues (set up notifications)
   - Check PyPI download errors
   - Monitor user feedback channels

2. **Quick response plan**
   - Team member available for emergencies
   - Rollback procedure documentation ready
   - Communication templates prepared

3. **Gradual rollout for major changes**
   - Beta releases for testing
   - Pre-release tags (v2.0.0-beta.1)
   - Community testing period

## Emergency Contacts

- **Maintainer**: caokai_cgs@163.com
- **GitHub Issues**: https://github.com/KaiTastic/pyASDReader/issues
- **PyPI Support**: https://pypi.org/help/

## Rollback Checklist

- [ ] Issue documented in GitHub
- [ ] Last good version identified
- [ ] User announcement posted
- [ ] Bad version yanked/deleted on PyPI
- [ ] Hotfix or rollback tag created
- [ ] Release verified on PyPI
- [ ] Installation tested in clean environment
- [ ] CHANGELOG updated
- [ ] Dev branch synced
- [ ] Post-mortem scheduled
- [ ] Prevention measures identified

## Additional Resources

- [VERSION_MANAGEMENT.md](https://github.com/KaiTastic/pyASDReader/blob/main/VERSION_MANAGEMENT.md) - Normal release workflow
- [RELEASE_EXAMPLES](RELEASE_EXAMPLES.html) - Release scenarios
- [PyPI Package Management](https://pypi.org/manage/project/pyASDReader/)
- [GitHub Releases](https://github.com/KaiTastic/pyASDReader/releases)

## Key Differences: Yank vs Delete

| Action | Yank | Delete |
|--------|------|--------|
| **Visibility** | Visible with warning | Completely gone |
| **Can reinstall** | Yes (with flag) | No (404 error) |
| **Reversible** | Yes | No (permanent) |
| **Version number** | Preserved | Lost forever |
| **pip behavior** | Skips by default | Not found |
| **Best for** | Most situations | Extreme cases only |

**Recommendation**: Always yank first. Only delete if absolutely necessary (e.g., security issue with exposed credentials).

---

**Last Updated**: 2025-10-07
**Version**: 2.0 (Streamlined)

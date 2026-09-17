# API Token Fallback Setup

Use this guide if Trusted Publishing is not available or as a temporary fallback.

## When to Use API Tokens

- ✅ Working with forked repositories (OIDC not supported)
- ✅ Temporary fallback during Trusted Publishing issues
- ✅ Local testing/development
- ❌ Not recommended for production (use Trusted Publishing instead)

---

## Setup Steps

### 1. Generate PyPI API Token

1. Log in to [PyPI](https://pypi.org/)

2. Navigate to Account Settings → API tokens:
   ```
   https://pypi.org/manage/account/token/
   ```

3. Click **"Add API token"**

4. Configure token:
   ```
   Token name: GitHub Actions - pyASDReader
   Scope: Project: pyASDReader (recommended)
           OR
           Entire account (all projects) - if project-specific unavailable
   ```

5. Click **"Create token"**

6. **IMPORTANT**: Copy the token immediately
   - Starts with `pypi-`
   - You'll never see it again
   - Store securely

### 2. Add Token to GitHub Secrets

**Option A: Via GitHub CLI**
```bash
gh secret set PYPI_API_TOKEN
# Paste token when prompted
```

**Option B: Via Web UI**
1. Go to repository settings:
   ```
   https://github.com/KaiTastic/pyASDReader/settings/secrets/actions
   ```

2. Click **"New repository secret"**

3. Fill in:
   ```
   Name: PYPI_API_TOKEN
   Value: pypi-...your token...
   ```

4. Click **"Add secret"**

### 3. Update Workflow

Edit `.github/workflows/publish-to-pypi.yml`:

```yaml
publish-to-pypi:
  name: Publish to PyPI
  runs-on: ubuntu-latest

  # Keep environment for approval workflow
  environment:
    name: pypi-production
    url: https://pypi.org/project/pyASDReader/

  permissions:
    id-token: write  # Keep for future Trusted Publishing

  steps:
    - name: Download distribution packages
      uses: actions/download-artifact@v4
      with:
        name: python-package-distributions
        path: dist/

    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        password: ${{ secrets.PYPI_API_TOKEN }}  # Add this line
        verbose: true
```

### 4. Test

```bash
git add .github/workflows/publish-to-pypi.yml
git commit -m "feat: Add API token fallback for PyPI publishing"
git push

# Test with a tag
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

---

## TestPyPI Setup

Same process for TestPyPI:

### 1. Generate TestPyPI Token

```
https://test.pypi.org/manage/account/token/
```

### 2. Add to GitHub Secrets

```bash
gh secret set TESTPYPI_API_TOKEN
```

### 3. Update Workflow

Edit `.github/workflows/publish-to-testpypi.yml`:

```yaml
- name: Publish to TestPyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    repository-url: https://test.pypi.org/legacy/
    password: ${{ secrets.TESTPYPI_API_TOKEN }}  # Add this
    skip-existing: true
    verbose: true
```

---

## Migration Back to Trusted Publishing

Once Trusted Publishing is working, migrate back:

### 1. Configure Trusted Publishing

Follow [TRUSTED_PUBLISHING_SETUP](./TRUSTED_PUBLISHING_SETUP.html)

### 2. Test with Both Methods

```yaml
- name: Publish to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    password: ${{ secrets.PYPI_API_TOKEN }}  # Fallback
    verbose: true
# Trusted Publishing tries first, falls back to password if OIDC fails
```

### 3. Remove API Token

Once Trusted Publishing is confirmed working:

```yaml
- name: Publish to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    verbose: true
    # No password - Trusted Publishing only
```

### 4. Rotate Token

```
1. Delete token from PyPI
2. Remove from GitHub Secrets: Settings → Secrets → PYPI_API_TOKEN → Remove
3. Update any local scripts that used it
```

---

## Security Best Practices

### Token Management

- 🔒 Use project-scoped tokens (not account-wide)
- ⏰ Rotate tokens quarterly
- 📝 Document token purpose and owner
- 🗑️ Delete unused tokens immediately
- 🚫 Never commit tokens to code

### GitHub Secrets

- ✅ Use repository secrets (not environment secrets for tokens)
- ✅ Limit secret access to necessary workflows
- ✅ Audit secret access regularly
- ✅ Use short-lived tokens when possible

### Monitoring

- 📊 Review PyPI project activity regularly
- 🔍 Check GitHub Actions logs for unauthorized use
- ⚠️ Set up alerts for unexpected publishes
- 🔔 Monitor for token leakage (GitHub secret scanning)

---

## Troubleshooting

### Error: "403 Invalid or non-existent authentication"

**Cause**: Token is invalid, expired, or not properly set

**Fix**:
1. Verify secret exists: `gh secret list`
2. Regenerate token on PyPI
3. Update GitHub Secret
4. Retry workflow

### Error: "400 File already exists"

**Cause**: Version already published to PyPI

**Fix**:
1. Check PyPI to confirm version exists
2. Increment version number
3. Use `skip-existing: true` for TestPyPI

### Error: "Token not found"

**Cause**: Secret name mismatch in workflow

**Fix**:
1. Check secret name: `gh secret list`
2. Verify workflow uses correct name: `${{ secrets.PYPI_API_TOKEN }}`
3. Ensure no typos

---

## Comparison: API Token vs Trusted Publishing

| Feature | API Token | Trusted Publishing |
|---------|-----------|-------------------|
| **Security** | ⚠️ Long-lived credentials | ✅ Short-lived, auto-expiring |
| **Setup** | ✅ Simple | ⚠️ Requires configuration |
| **Maintenance** | ⚠️ Manual rotation needed | ✅ No maintenance |
| **Auditability** | ⚠️ Limited traceability | ✅ Full GitHub integration |
| **Secrets Management** | ⚠️ Manual storage | ✅ No secrets needed |
| **Fork Support** | ✅ Works in forks | ❌ Doesn't work in forks |
| **Recommendation** | Fallback only | ✅ Primary method |

---

## Quick Reference Commands

```bash
# Generate token
# → Visit PyPI/TestPyPI web UI

# Add secret via CLI
gh secret set PYPI_API_TOKEN
gh secret set TESTPYPI_API_TOKEN

# List secrets
gh secret list

# Remove secret
gh secret remove PYPI_API_TOKEN

# Test workflow
git tag -a vX.X.X -m "Test"
git push origin vX.X.X

# View workflow logs
gh run list --workflow=publish-to-pypi.yml
gh run view --log
```

---

## Related Documentation

- [Trusted Publishing Setup](./TRUSTED_PUBLISHING_SETUP.html) - Recommended primary method
- [Troubleshooting Guide](./TROUBLESHOOTING_TRUSTED_PUBLISHING.html) - Common issues
- [Version Management](https://github.com/KaiTastic/pyASDReader/blob/main/VERSION_MANAGEMENT.md) - Release workflow

---

**Last Updated**: October 7, 2025
**Version**: 1.0
**Maintained by**: pyASDReader Development Team

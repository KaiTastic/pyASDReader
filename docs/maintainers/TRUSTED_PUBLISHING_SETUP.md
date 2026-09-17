# Trusted Publishing Setup Guide

## Overview

Trusted Publishing (also known as OIDC publishing) is a secure, token-less authentication method for publishing Python packages to PyPI. It eliminates the need to manage long-lived API tokens by using short-lived, automatically generated tokens from GitHub Actions.

## Why Use Trusted Publishing?

### Advantages over API Tokens

✅ **More Secure**
- No long-lived credentials to manage
- Tokens automatically expire after use
- Reduced risk of credential leakage

✅ **Easier Management**
- No manual token rotation needed
- No secrets to store in GitHub
- Automatically tied to specific workflows

✅ **Better Auditability**
- Clear association with GitHub Actions runs
- Easier to track which workflow published which version
- Integrated with GitHub's audit logs

### How It Works

```
┌─────────────────┐
│  GitHub Actions │
│   Workflow Run  │
└────────┬────────┘
         │
         │ 1. Request OIDC token
         ▼
┌─────────────────┐
│  GitHub OIDC    │
│  Token Service  │
└────────┬────────┘
         │
         │ 2. Token with claims:
         │    - repository: KaiTastic/pyASDReader
         │    - workflow: publish-to-pypi.yml
         │    - environment: pypi-production
         ▼
┌─────────────────┐
│   PyPI OIDC     │
│   Verification  │
└────────┬────────┘
         │
         │ 3. Verify claims match
         │    configured publisher
         ▼
┌─────────────────┐
│  Package Upload │
│    Authorized   │
└─────────────────┘
```

---

## Prerequisites

Before configuring Trusted Publishing, ensure you have:

- [ ] Published at least one version of your package to PyPI manually
- [ ] Admin access to the PyPI project
- [ ] Admin access to the GitHub repository
- [ ] Created GitHub Environment (if using environments)

---

## Part 1: PyPI Configuration

### Step 1: Access PyPI Publishing Settings

1. Log in to [PyPI](https://pypi.org/)

2. Navigate to your project settings:
   ```
   https://pypi.org/manage/project/pyASDReader/settings/publishing/
   ```

3. Scroll to the "Trusted Publishers" section

### Step 2: Add GitHub as Trusted Publisher

Click the **"Add a new publisher"** button.

### Step 3: Fill in Configuration

⚠️ **CRITICAL**: These values must EXACTLY match your GitHub repository and workflow configuration.

Fill in the form:

```yaml
PyPI project name: pyASDReader
```
_This is the package name as registered on PyPI_

```yaml
Owner: KaiTastic
```
_This is your GitHub username or organization name_
_⚠️ Case-sensitive! Must match exactly_

```yaml
Repository name: pyASDReader
```
_This is your GitHub repository name_
_⚠️ NOT the full path like "KaiTastic/pyASDReader"_
_⚠️ NOT the directory name like "ASD_File_Reader"_

```yaml
Workflow name: publish-to-pypi.yml
```
_This is the workflow filename only_
_⚠️ Do NOT include the path like ".github/workflows/publish-to-pypi.yml"_
_⚠️ Must include the .yml extension_

```yaml
Environment name: pypi-production
```
_This is the GitHub Environment name_
_⚠️ Leave blank if your workflow doesn't use environments_
_⚠️ Must match the `environment.name` in your workflow_

### Step 4: Save Configuration

Click **"Add"** or **"Save"**.

You should see your new trusted publisher listed with:
- ✅ Status: "Pending first use" or "Active"
- 📝 Details showing all configured values

### Step 5: Verify Configuration

Double-check that the saved configuration shows:

```
GitHub
├─ Owner: KaiTastic
├─ Repository: pyASDReader
├─ Workflow: publish-to-pypi.yml
└─ Environment: pypi-production
```

---

## Part 2: TestPyPI Configuration (Recommended)

It's highly recommended to set up TestPyPI first for testing.

### Step 1: Access TestPyPI Publishing Settings

1. Log in to [TestPyPI](https://test.pypi.org/)

2. Navigate to your project settings:
   ```
   https://test.pypi.org/manage/project/pyASDReader/settings/publishing/
   ```

### Step 2: Add GitHub as Trusted Publisher

Use the **same configuration** as PyPI, except:

```yaml
Workflow name: publish-to-testpypi.yml
```
_Use the TestPyPI workflow filename_

### Step 3: Test Configuration

After setting up TestPyPI:

```bash
# Push to dev branch to trigger TestPyPI publish
git checkout dev
git push origin dev

# Watch the workflow
gh run watch
```

If TestPyPI publishing succeeds, your configuration is correct!

---

## Part 3: GitHub Environment Setup

### When to Use Environments

Use GitHub Environments if you want:
- Manual approval before publishing
- Deployment restrictions (e.g., only from main branch)
- Environment-specific secrets

### Step 1: Create Environment

1. Navigate to GitHub repository settings:
   ```
   https://github.com/KaiTastic/pyASDReader/settings/environments
   ```

2. Click **"New environment"**

3. Enter name: `pypi-production`

### Step 2: Configure Protection Rules

#### Required Reviewers (Recommended)

1. Enable **"Required reviewers"**
2. Add yourself and/or team members
3. Consider enabling **"Prevent self-review"** if you have multiple maintainers

**Why this matters**: Prevents accidental or unauthorized deployments

#### Wait Timer (Optional)

1. Enable **"Wait timer"**
2. Set delay (e.g., 5 minutes)

**Use case**: Gives you time to cancel a deployment if a mistake is detected

#### Deployment Branches (Recommended)

1. Enable **"Deployment branches"**
2. Select **"Selected branches"**
3. Add rule: `main`

**Why this matters**: Ensures production releases only come from the main branch

### Step 3: Save Configuration

Click **"Save protection rules"**

---

## Part 4: Workflow Configuration

### Verify Workflow File

Your workflow should have these key elements:

```yaml
name: Publish to PyPI (Production Release)

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  publish-to-pypi:
    name: Publish to PyPI
    runs-on: ubuntu-latest

    # If using GitHub Environment
    environment:
      name: pypi-production
      url: https://pypi.org/project/pyASDReader/

    permissions:
      id-token: write  # REQUIRED for trusted publishing

    steps:
    - name: Publish to PyPI
      uses: pypa/gh-action-pypi-publish@release/v1
      with:
        verbose: true
        # NO password needed for trusted publishing!
```

### Common Mistakes to Avoid

❌ **Don't include password parameter**
```yaml
# WRONG - Don't do this with trusted publishing
- uses: pypa/gh-action-pypi-publish@release/v1
  with:
    password: ${{ secrets.PYPI_API_TOKEN }}  # Remove this line
```

❌ **Don't forget id-token permission**
```yaml
# WRONG - Missing required permission
permissions:
  contents: write  # Not enough!
```

✅ **Correct configuration**
```yaml
# RIGHT - id-token permission required
permissions:
  id-token: write
```

❌ **Don't mismatch environment name**
```yaml
# PyPI configured with: pypi-production
# Workflow uses: production  ❌ WRONG!

# Must match exactly:
environment:
  name: pypi-production  # ✅ CORRECT
```

---

## Part 5: Testing the Setup

### Test 1: Diagnostic Script

Run the local diagnostic script:

```bash
bash scripts/test_environment_setup.sh
```

Expected output:
```
✓ GitHub CLI installed
✓ Authenticated with GitHub
✓ Environment 'pypi-production' exists
✓ Required reviewers: 1 configured
✓ Deployment branch restriction: Enabled
✓ Workflow correctly references 'pypi-production' environment
✓ Workflow configured for OIDC Trusted Publishing
```

### Test 2: TestPyPI Publish

```bash
# Push to dev branch
git checkout dev
git push origin dev

# Watch workflow
gh run watch
```

Check for success message:
```
✓ Successfully authenticated via OIDC
✓ Uploading distributions to https://test.pypi.org/legacy/
✓ Package published successfully
```

### Test 3: PyPI Publish (Dry Run)

Create a test tag:

```bash
git checkout main
git tag -a v0.0.0-test -m "Test Trusted Publishing"
git push origin v0.0.0-test
```

**Important**: Use a version that doesn't exist to avoid conflicts.

Watch the workflow:
```bash
gh run watch
```

If successful, delete the test tag:
```bash
git tag -d v0.0.0-test
git push origin :refs/tags/v0.0.0-test
```

---

## Troubleshooting

### Error: "Trusted publishing exchange failure"

**Cause**: PyPI configuration doesn't match workflow

**Fix**:
1. Double-check PyPI configuration matches exactly:
   - Owner: `KaiTastic`
   - Repository: `pyASDReader` (not `ASD_File_Reader`)
   - Workflow: `publish-to-pypi.yml` (not path)
   - Environment: `pypi-production` (or empty if not using)

2. Verify GitHub Environment exists if configured

3. Check workflow has `id-token: write` permission

### Error: "Environment protection rules prevent deployment"

**Cause**: Deployment blocked by protection rules

**Fix**:
1. Check tag was pushed to `main` branch (if branch restriction enabled)
2. Approve deployment in GitHub Actions UI
3. Ensure you're a configured reviewer

### Error: "Token request failed"

**Cause**: GitHub OIDC token couldn't be generated

**Fix**:
1. Verify `id-token: write` permission in workflow
2. Check repository is not a fork (OIDC not supported in forks)
3. Ensure workflow is running in correct context

### Error: "Audience claim mismatch"

**Cause**: Token audience doesn't match PyPI

**Fix**:
1. This usually indicates a PyPA action version mismatch
2. Update to latest: `pypa/gh-action-pypi-publish@release/v1`
3. Check for custom audience configuration

### Error: "Subject claim mismatch"

**Cause**: Repository/workflow/environment don't match

**Fix**:
1. Print token claims for debugging:
   ```bash
   gh workflow run debug-trusted-publishing.yml
   ```
2. Compare claims to PyPI configuration
3. Adjust PyPI configuration to match claims

---

## Security Best Practices

### Do's ✅

- ✅ Use Trusted Publishing for all new projects
- ✅ Restrict deployments to `main` branch only
- ✅ Require manual approval for production deployments
- ✅ Test with TestPyPI before configuring PyPI
- ✅ Regularly review deployment logs
- ✅ Use semantic version tags only (v1.2.3)

### Don'ts ❌

- ❌ Don't mix Trusted Publishing with API tokens
- ❌ Don't disable branch protection for deployments
- ❌ Don't skip TestPyPI testing
- ❌ Don't use Trusted Publishing in forked repositories
- ❌ Don't share the same environment for test and prod
- ❌ Don't configure multiple publishers for same workflow

---

## Migration from API Tokens

If you're currently using API tokens, here's how to migrate:

### Step 1: Configure Trusted Publishing

Follow Parts 1-4 above.

### Step 2: Test Both Methods

Keep the API token as backup while testing:

```yaml
- name: Publish to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    # Trusted publishing tries first
    # Falls back to password if OIDC fails
    password: ${{ secrets.PYPI_API_TOKEN }}  # Fallback
    verbose: true
```

### Step 3: Verify Trusted Publishing Works

Check workflow logs for:
```
Trusted publishing authentication successful
```

### Step 4: Remove API Token

Once confirmed working, remove the password line:

```yaml
- name: Publish to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
  with:
    verbose: true
    # Password removed - using trusted publishing only
```

### Step 5: Rotate API Token

After migration, rotate your old API token:
1. Delete the token from PyPI
2. Remove from GitHub Secrets
3. Update any local scripts that used it

---

## Reference: Configuration Matrix

| Component | Setting | Value |
|-----------|---------|-------|
| **PyPI** | Project name | `pyASDReader` |
| | Owner | `KaiTastic` |
| | Repository | `pyASDReader` |
| | Workflow | `publish-to-pypi.yml` |
| | Environment | `pypi-production` |
| **TestPyPI** | Project name | `pyASDReader` |
| | Owner | `KaiTastic` |
| | Repository | `pyASDReader` |
| | Workflow | `publish-to-testpypi.yml` |
| | Environment | _(empty)_ |
| **GitHub Environment** | Name | `pypi-production` |
| | Deployment branches | `main` |
| | Required reviewers | 1+ |
| **Workflow** | Permission | `id-token: write` |
| | Environment reference | `pypi-production` |

---

## Additional Resources

- [PyPI Trusted Publishers Documentation](https://docs.pypi.org/trusted-publishers/)
- [GitHub OIDC Documentation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [PyPA Publish Action](https://github.com/pypa/gh-action-pypi-publish)
- [Project Troubleshooting Guide](./TROUBLESHOOTING_TRUSTED_PUBLISHING.md)

---

## Support

If you encounter issues:

1. **Check diagnostics**: Run `bash scripts/test_environment_setup.sh`
2. **Review logs**: Check GitHub Actions workflow logs
3. **Compare configuration**: Use the Configuration Matrix above
4. **Run debug workflow**: `gh workflow run debug-trusted-publishing.yml`
5. **Consult troubleshooting**: See [TROUBLESHOOTING_TRUSTED_PUBLISHING](./TROUBLESHOOTING_TRUSTED_PUBLISHING.md)
6. **Open issue**: If problems persist, open a GitHub issue with diagnostic output

---

**Last Updated**: October 7, 2025
**Version**: 1.0
**Maintained by**: pyASDReader Development Team

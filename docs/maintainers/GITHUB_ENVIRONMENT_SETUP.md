# GitHub Environment Setup for Production Deployments

This document explains how to configure GitHub Environments for PyPI production deployments with manual approval protection.

## Why Use Environments?

GitHub Environments provide:
- **Manual approval gates** for production deployments
- **Environment-specific secrets** (API tokens, credentials)
- **Deployment branch restrictions** (e.g., only from `main`)
- **Deployment history and logs**
- **Protection against accidental releases**

## Prerequisites

- Repository must be **public** (for GitHub Free plan)
- You must have **repository admin access**
- For private repositories, requires GitHub Pro, Team, or Enterprise

## Setup Instructions

### Step 1: Access Environment Settings

1. Go to your GitHub repository
2. Click **Settings** (top menu)
3. In the left sidebar, click **Environments**
4. Click **New environment**

### Step 2: Create PyPI Production Environment

1. Enter environment name: `pypi-production`
2. Click **Configure environment**

### Step 3: Configure Protection Rules

#### Required Reviewers (Recommended)

1. Under **Deployment protection rules**, enable **Required reviewers**
2. Click **Add up to 6 people or teams**
3. Add yourself and/or team members who should approve releases
4. **Important**: Enable **Prevent self-review** if you have multiple maintainers

**Why this matters**: Prevents accidental or unauthorized deployments to PyPI

#### Wait Timer (Optional)

1. Enable **Wait timer**
2. Set delay (e.g., 5 minutes)
3. Use case: Time to cancel deployment if mistake detected

#### Deployment Branches (Recommended)

1. Enable **Deployment branches**
2. Select **Selected branches**
3. Add rule: `main`

**Why this matters**: Ensures production releases only come from the main branch

### Step 4: Add Environment Secrets

1. Scroll to **Environment secrets**
2. Click **Add secret**
3. Add your PyPI API token:
   - Name: `PYPI_API_TOKEN`
   - Value: Your PyPI API token

**Note**: Environment secrets override repository secrets when the environment is active.

### Step 5: Update Workflow Configuration

The `publish-to-pypi.yml` workflow already has environment configuration commented out:

```yaml
# Uncomment these lines:
environment:
  name: pypi-production
  url: https://pypi.org/project/pyASDReader/
```

**Edit `.github/workflows/publish-to-pypi.yml`**:

```yaml
publish-to-pypi:
  name: Publish to PyPI
  needs: [build]
  runs-on: ubuntu-latest

  # Enable environment protection
  environment:
    name: pypi-production
    url: https://pypi.org/project/pyASDReader/

  permissions:
    id-token: write  # Required for trusted publishing

  steps:
    # ... rest of the workflow
```

### Step 6: Test the Setup

1. Create a test tag: `git tag -a v0.0.0-test -m "Test release"`
2. Push the tag: `git push origin v0.0.0-test`
3. Go to Actions tab and observe:
   - Workflow starts automatically
   - Pauses at **publish-to-pypi** job
   - Shows "Waiting for approval"
4. Click **Review deployments** button
5. Select reviewers and approve/reject
6. **Delete test tag** after verification:
   ```bash
   git tag -d v0.0.0-test
   git push origin :refs/tags/v0.0.0-test
   ```

## Approval Workflow

When a release is triggered:

1. **Workflow starts**: Tag push triggers `publish-to-pypi.yml`
2. **Build phase completes**: Package is built and validated
3. **Deployment pauses**: Waits for manual approval
4. **Notification sent**: Configured reviewers receive notification
5. **Reviewer approves**: Clicks "Review deployments" -> "Approve and deploy"
6. **Deployment proceeds**: Package is published to PyPI
7. **GitHub Release created**: Automated release notes generated

## Screenshots Guide

### 1. Environment Creation
![Environment setup](https://docs.github.com/assets/cb-24785/images/help/actions/environment-create.png)

### 2. Protection Rules
![Protection rules](https://docs.github.com/assets/cb-47896/images/help/actions/environment-deployment-protection-rules.png)

### 3. Deployment Approval
![Approval UI](https://docs.github.com/assets/cb-51508/images/help/actions/review-deployment.png)

## Troubleshooting

### Problem: Environment not showing in workflow

**Solution**:
- Ensure environment name matches exactly: `pypi-production`
- Check workflow syntax is correct
- Verify you have admin access

### Problem: No approval notification received

**Solution**:
- Check GitHub notification settings
- Ensure reviewer has access to repository
- Try mentioning reviewer explicitly in commit message

### Problem: Approval button not appearing

**Solution**:
- Refresh the Actions page
- Check that required reviewers are properly configured
- Verify you're viewing the correct workflow run

### Problem: "Secret not found" error

**Solution**:
- Verify `PYPI_API_TOKEN` is added to environment secrets (not just repository secrets)
- Check secret name matches exactly
- Regenerate PyPI token if needed

## Best Practices

1. **Multiple Reviewers**: Add 2-3 trusted reviewers for redundancy
2. **Self-Review Prevention**: Enable if you have co-maintainers
3. **Branch Protection**: Restrict deployments to `main` branch only
4. **Regular Audits**: Review deployment history monthly
5. **Token Rotation**: Rotate PyPI API tokens quarterly
6. **Documentation**: Keep this document updated with any changes

## Security Considerations

1. **Never commit tokens**: Use GitHub secrets only
2. **Scope tokens appropriately**: PyPI token should only have upload permissions
3. **Review deployment logs**: Check for suspicious activity
4. **Enable 2FA**: On both GitHub and PyPI accounts
5. **Audit access regularly**: Remove inactive reviewers

## Alternative: Trusted Publishers (Recommended)

GitHub Actions supports PyPI's **Trusted Publishers** feature, which doesn't require API tokens:

1. Go to PyPI project settings
2. Add GitHub as a trusted publisher
3. Configure: `KaiTastic/pyASDReader` from workflow `publish-to-pypi.yml`
4. Remove `password:` line from workflow
5. PyPI will automatically authenticate via OIDC

**Benefits**: More secure, no token management needed

See: https://docs.pypi.org/trusted-publishers/

## References

- [GitHub Environments Documentation](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions Security Best Practices](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

## Summary

With GitHub Environments configured:
- ✅ Manual approval required for production releases
- ✅ Prevents accidental deployments
- ✅ Provides deployment audit trail
- ✅ Environment-specific secrets management
- ✅ Branch-based deployment restrictions

**Estimated setup time**: 10-15 minutes
**Maintenance overhead**: Minimal (quarterly token rotation)

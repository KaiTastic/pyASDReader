#!/bin/bash
#
# Trusted Publishing Diagnostic Script
# Usage: bash scripts/diagnose_trusted_publishing.sh
#
# This script checks Trusted Publishing configuration and provides recommendations

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "========================================"
echo "Trusted Publishing Diagnostic"
echo "========================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check gh CLI
if ! command -v gh &> /dev/null; then
    echo -e "${RED}✗ GitHub CLI (gh) not installed${NC}"
    echo "Install with: brew install gh"
    exit 1
fi
echo -e "${GREEN}✓ GitHub CLI installed${NC}"

# Check authentication
if ! gh auth status &> /dev/null; then
    echo -e "${RED}✗ Not authenticated with GitHub${NC}"
    echo "Authenticate with: gh auth login"
    exit 1
fi
echo -e "${GREEN}✓ Authenticated with GitHub${NC}"

# Get repository info
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
OWNER=$(echo "$REPO" | cut -d'/' -f1)
REPO_NAME=$(echo "$REPO" | cut -d'/' -f2)

echo -e "${GREEN}✓ Repository: $REPO${NC}"
echo ""

# === Workflow Configuration Check ===
echo "=== Checking Workflow Configuration ==="
echo ""

PYPI_WORKFLOW=".github/workflows/publish-to-pypi.yml"
TESTPYPI_WORKFLOW=".github/workflows/publish-to-testpypi.yml"

if [ -f "$PYPI_WORKFLOW" ]; then
    echo -e "${GREEN}✓ PyPI workflow found${NC}"

    # Check for id-token permission
    if grep -q "id-token: write" "$PYPI_WORKFLOW"; then
        echo -e "${GREEN}✓ id-token: write permission configured${NC}"
    else
        echo -e "${RED}✗ id-token: write permission missing${NC}"
        echo "  Add to workflow:"
        echo "    permissions:"
        echo "      id-token: write"
    fi

    # Check for environment
    if grep -q "environment:" "$PYPI_WORKFLOW"; then
        ENV_NAME=$(grep -A1 "environment:" "$PYPI_WORKFLOW" | grep "name:" | sed 's/.*name:\s*//' | tr -d ' ')
        echo -e "${GREEN}✓ Environment configured: $ENV_NAME${NC}"
    else
        echo -e "${YELLOW}⚠ No environment configured${NC}"
        ENV_NAME=""
    fi

    # Check for password (shouldn't be there for pure trusted publishing)
    if grep -A5 "gh-action-pypi-publish" "$PYPI_WORKFLOW" | grep -q "password:"; then
        echo -e "${YELLOW}⚠ API token (password) found in workflow${NC}"
        echo "  This is OK if using hybrid approach (fallback)"
        echo "  For pure Trusted Publishing, remove password line"
    else
        echo -e "${GREEN}✓ Using pure Trusted Publishing (no password)${NC}"
    fi
else
    echo -e "${RED}✗ PyPI workflow not found: $PYPI_WORKFLOW${NC}"
fi

echo ""

# === GitHub Environment Check ===
echo "=== Checking GitHub Environment ==="
echo ""

if [ -n "$ENV_NAME" ]; then
    if gh api repos/$REPO/environments/$ENV_NAME &> /dev/null; then
        echo -e "${GREEN}✓ Environment '$ENV_NAME' exists${NC}"

        # Get environment details
        ENV_DATA=$(gh api repos/$REPO/environments/$ENV_NAME)

        # Check reviewers
        REVIEWER_COUNT=$(echo "$ENV_DATA" | jq '.protection_rules[] | select(.type == "required_reviewers") | .reviewers | length' 2>/dev/null || echo "0")
        if [ "$REVIEWER_COUNT" -gt 0 ]; then
            echo -e "${GREEN}✓ Required reviewers: $REVIEWER_COUNT configured${NC}"
        else
            echo -e "${YELLOW}⚠ No required reviewers configured${NC}"
            echo "  Recommendation: Add at least 1 reviewer for production"
        fi

        # Check branch policy
        BRANCH_POLICY=$(echo "$ENV_DATA" | jq -r '.deployment_branch_policy.protected_branches' 2>/dev/null || echo "false")
        if [ "$BRANCH_POLICY" = "true" ]; then
            echo -e "${GREEN}✓ Deployment branch restriction: Enabled${NC}"
        else
            echo -e "${YELLOW}⚠ No branch restriction${NC}"
            echo "  Recommendation: Restrict to 'main' branch only"
        fi
    else
        echo -e "${RED}✗ Environment '$ENV_NAME' not found${NC}"
        echo "  Create at: https://github.com/$REPO/settings/environments"
    fi
else
    echo -e "${YELLOW}⚠ No environment used in workflow${NC}"
fi

echo ""

# === PyPI Configuration Check ===
echo "=== PyPI Configuration Requirement ==="
echo ""
echo "Your PyPI Trusted Publisher should be configured with:"
echo ""
echo -e "  ${BLUE}Owner:${NC} $OWNER"
echo -e "  ${BLUE}Repository name:${NC} $REPO_NAME"
echo -e "  ${BLUE}Workflow name:${NC} publish-to-pypi.yml"
echo -e "  ${BLUE}Environment name:${NC} ${ENV_NAME:-(empty)}"
echo ""
echo "Verify at: https://pypi.org/manage/project/pyASDReader/settings/publishing/"
echo ""

# === TestPyPI Configuration ===
echo "=== TestPyPI Configuration Requirement ==="
echo ""
echo "Your TestPyPI Trusted Publisher should be configured with:"
echo ""
echo -e "  ${BLUE}Owner:${NC} $OWNER"
echo -e "  ${BLUE}Repository name:${NC} $REPO_NAME"
echo -e "  ${BLUE}Workflow name:${NC} publish-to-testpypi.yml"
echo -e "  ${BLUE}Environment name:${NC} (empty - no environment)"
echo ""
echo "Verify at: https://test.pypi.org/manage/project/pyASDReader/settings/publishing/"
echo ""

# === API Reachability Test ===
echo "=== Testing API Reachability ==="
echo ""

if curl -sSf https://pypi.org/pypi/pyASDReader/json > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PyPI API is accessible${NC}"
else
    echo -e "${YELLOW}⚠ Could not reach PyPI API${NC}"
fi

if curl -sSf https://test.pypi.org/pypi/pyASDReader/json > /dev/null 2>&1; then
    echo -e "${GREEN}✓ TestPyPI API is accessible${NC}"
else
    echo -e "${YELLOW}⚠ Could not reach TestPyPI API${NC}"
fi

echo ""

# === Recent Workflow Runs ===
echo "=== Recent Workflow Runs ==="
echo ""

echo "PyPI Workflow (last 5 runs):"
gh run list --workflow=publish-to-pypi.yml --limit=5 --json status,conclusion,createdAt,headBranch | \
    jq -r '.[] | "  \(.createdAt | split("T")[0]) | \(.headBranch) | \(.status) | \(.conclusion // "running")"' || \
    echo "  No recent runs found"

echo ""

# === Summary and Recommendations ===
echo "============================================"
echo "  Summary and Recommendations"
echo "============================================"
echo ""

echo "Quick Actions:"
echo ""
echo "1. Verify PyPI Configuration:"
echo "   https://pypi.org/manage/project/pyASDReader/settings/publishing/"
echo ""
echo "2. Check GitHub Environment (if using):"
echo "   https://github.com/$REPO/settings/environments"
echo ""
echo "3. Run diagnostic workflow:"
echo "   gh workflow run debug-trusted-publishing.yml"
echo ""
echo "4. View recent failures:"
echo "   gh run list --workflow=publish-to-pypi.yml --status=failure --limit=1"
echo "   gh run view --log-failed"
echo ""
echo "5. Read documentation:"
echo "   docs/maintainers/TRUSTED_PUBLISHING_SETUP.md"
echo "   docs/maintainers/TROUBLESHOOTING_TRUSTED_PUBLISHING.md"
echo ""

echo "============================================"
echo ""

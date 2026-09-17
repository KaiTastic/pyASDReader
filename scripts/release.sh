#!/bin/bash

# pyASDReader Automated Release Script v2.1
# Usage:
#   bash scripts/release.sh <version> [options]
#   version: "patch", "minor", "major", or specific version like "1.2.4"
#
# Options:
#   --dry-run       Preview actions without executing
#   --yes          Skip all confirmation prompts
#   --skip-tests   Skip running test suite (not recommended)
#
# Examples:
#   bash scripts/release.sh patch              # Runs tests by default
#   bash scripts/release.sh minor --dry-run    # Preview without changes
#   bash scripts/release.sh 1.2.4 --yes        # Auto-approve, still runs tests
#   bash scripts/release.sh patch --skip-tests # Skip tests (not recommended)
#
# This script automates the release workflow using Python tools:
#   - scripts/validate_release.py
#   - scripts/utils/changelog_manager.py

set -e  # Exit on error

# Parse arguments
VERSION_ARG=""
DRY_RUN=false
AUTO_YES=false
SKIP_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --yes|-y)
            AUTO_YES=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --rollback)
            ROLLBACK_MODE=true
            shift
            ;;
        --resume)
            RESUME_MODE=true
            shift
            ;;
        --help|-h)
            cat << EOF
Usage: bash scripts/release.sh <version> [options]

Arguments:
  version         "patch", "minor", "major", or specific version (e.g., "1.2.4")

Options:
  --dry-run       Preview actions without making changes
  --yes, -y       Skip confirmation prompts (auto-approve)
  --skip-tests    Skip test suite execution (not recommended)
  --help, -h      Show this help message

Examples:
  bash scripts/release.sh patch           # Increment patch version (runs tests)
  bash scripts/release.sh minor --dry-run # Preview minor version bump
  bash scripts/release.sh 1.2.4 --yes     # Release v1.2.4 without prompts (runs tests)

Documentation:
  - VERSION_MANAGEMENT.md - Release workflow guide
    - docs/maintainers/RELEASE_EXAMPLES.md - Detailed examples
    - docs/maintainers/CI_CD_WORKFLOWS.md - CI/CD information

Manual Rollback (if needed):
  git checkout dev
  git reset --soft HEAD~1    # Undo commit
  git checkout -- CHANGELOG.md  # Restore CHANGELOG
  git tag -d v1.2.3          # Delete local tag
  git push origin :refs/tags/v1.2.3  # Delete remote tag
EOF
            exit 0
            ;;
        -*)
            echo "Error: Unknown option $1"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            if [ -z "$VERSION_ARG" ]; then
                VERSION_ARG=$1
            else
                echo "Error: Multiple version arguments provided"
                exit 1
            fi
            shift
            ;;
    esac
done

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Print functions
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_step() {
    echo -e "\n${BLUE}==== $1 ====${NC}\n"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_dry_run() {
    echo -e "${CYAN}[DRY-RUN]${NC} Would execute: $1"
}

# State management functions
save_state() {
    local step=$1
    local data=$2
    if [ "$DRY_RUN" = false ]; then
        echo "$step|$data" > "$STATE_FILE"
        print_info "Checkpoint saved: $step"
    fi
}

load_state() {
    if [ -f "$STATE_FILE" ]; then
        cat "$STATE_FILE"
    fi
}

clear_state() {
    if [ -f "$STATE_FILE" ]; then
        rm "$STATE_FILE"
        print_info "State file cleared"
    fi
}

get_last_step() {
    if [ -f "$STATE_FILE" ]; then
        cut -d'|' -f1 "$STATE_FILE"
    else
        echo "none"
    fi
}

get_state_data() {
    if [ -f "$STATE_FILE" ]; then
        cut -d'|' -f2- "$STATE_FILE"
    fi
}

# Rollback function
perform_rollback() {
    print_step "Rollback Mode"

    if [ ! -f "$STATE_FILE" ]; then
        print_error "No state file found. Nothing to rollback."
        exit 1
    fi

    LAST_STEP=$(get_last_step)
    STATE_DATA=$(get_state_data)

    print_info "Last checkpoint: $LAST_STEP"
    print_info "State data: $STATE_DATA"
    echo ""

    case "$LAST_STEP" in
        "changelog_updated")
            print_info "Rolling back CHANGELOG changes..."
            if confirm "Restore CHANGELOG from git?"; then
                git checkout -- CHANGELOG.md
                print_success "CHANGELOG restored"
            fi
            ;;
        "committed")
            print_info "Rolling back last commit..."
            if confirm "Reset last commit (soft)?"; then
                git reset --soft HEAD~1
                print_success "Commit rolled back (changes preserved)"
            fi
            ;;
        "merged_to_main")
            print_error "Cannot automatically rollback merge to main"
            echo "Manual steps required:"
            echo "  1. git checkout main"
            echo "  2. git reset --hard origin/main  # If not pushed"
            echo "  3. git checkout dev"
            ;;
        "tagged")
            VERSION=$(echo "$STATE_DATA" | cut -d',' -f1)
            print_info "Rolling back tag: $VERSION"
            if confirm "Delete tag $VERSION?"; then
                git tag -d "$VERSION" || true
                git push origin ":refs/tags/$VERSION" 2>/dev/null || true
                print_success "Tag $VERSION deleted"
            fi
            ;;
        *)
            print_error "Unknown step: $LAST_STEP"
            ;;
    esac

    clear_state
    print_success "Rollback completed"
    exit 0
}

# Execute or preview command
execute_or_preview() {
    local description=$1
    shift

    if [ "$DRY_RUN" = true ]; then
        print_dry_run "$description"
        echo "  Command: $@"
    else
        "$@"
    fi
}

# Ask for confirmation
confirm() {
    if [ "$AUTO_YES" = true ] || [ "$DRY_RUN" = true ]; then
        return 0
    fi

    local prompt=$1
    local default=${2:-no}

    if [ "$default" = "yes" ]; then
        read -p "$prompt (yes/no) [yes]: " -r
        REPLY=${REPLY:-yes}
    else
        read -p "$prompt (yes/no) [no]: " -r
        REPLY=${REPLY:-no}
    fi

    [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]
}

# Validate arguments
if [ -z "$VERSION_ARG" ]; then
    print_error "Missing version argument"
    echo "Usage: bash scripts/release.sh <version> [options]"
    echo "Use --help for more information"
    exit 1
fi

# Get project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# State file for rollback/resume functionality
STATE_FILE="$PROJECT_ROOT/.release_state"

# Handle rollback mode
if [ "$ROLLBACK_MODE" = true ]; then
    perform_rollback
    # Will exit in perform_rollback function
fi

# Handle resume mode
if [ "$RESUME_MODE" = true ]; then
    if [ ! -f "$STATE_FILE" ]; then
        print_error "No state file found. Nothing to resume."
        exit 1
    fi
    LAST_STEP=$(get_last_step)
    print_info "Resuming from checkpoint: $LAST_STEP"
    echo ""
    # Continue execution below...
fi

# Dry-run banner
if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║        DRY-RUN MODE ACTIVE             ║"
    echo "║  No changes will be made to files      ║"
    echo "╚════════════════════════════════════════╝"
    echo ""
fi

print_step "Step 1: Pre-flight Checks"

# Check Python is available
if ! command -v python3 &> /dev/null; then
    print_error "python3 not found!"
    echo ""
    echo "📍 Python 3 is required to run the release tools."
    echo "💡 Install Python 3:"
    echo "   - macOS: brew install python3"
    echo "   - Ubuntu/Debian: sudo apt-get install python3"
    echo "   - Windows: Download from https://www.python.org/downloads/"
    exit 1
fi

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

if [ "$CURRENT_BRANCH" != "dev" ]; then
    print_warning "Current branch is '$CURRENT_BRANCH', expected 'dev'"
    echo ""
    echo "📍 Releases should typically be initiated from the 'dev' branch."
    echo "💡 To switch to dev branch:"
    echo "   git checkout dev"
    echo "   git pull origin dev"
    echo ""
    if ! confirm "Continue anyway?"; then
        print_info "Release cancelled"
        exit 0
    fi
else
    print_info "✓ On dev branch"
fi

# Calculate version type for semantic validation
# This will be determined after VERSION_ARG is parsed
VERSION_TYPE_ARG=""

# Run validation script (will be called after version is determined)

print_step "Step 2: Calculate Version Number"

# Get current version from git tags
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null | sed 's/^v//' || echo "0.0.0")
print_info "Current version: $CURRENT_VERSION"

# Calculate new version
if [[ "$VERSION_ARG" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    NEW_VERSION="$VERSION_ARG"
    VERSION_TYPE_ARG=""  # Unknown type for specific version
    print_info "Using specified version: $NEW_VERSION"
else
    IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

    case "$VERSION_ARG" in
        patch)
            PATCH=$((PATCH + 1))
            VERSION_TYPE_ARG="patch"
            ;;
        minor)
            MINOR=$((MINOR + 1))
            PATCH=0
            VERSION_TYPE_ARG="minor"
            ;;
        major)
            MAJOR=$((MAJOR + 1))
            MINOR=0
            PATCH=0
            VERSION_TYPE_ARG="major"
            ;;
        *)
            print_error "Invalid version argument: $VERSION_ARG"
            echo ""
            echo "📍 Version must be one of:"
            echo "   - 'patch'  : Increment patch version (1.2.3 → 1.2.4)"
            echo "   - 'minor'  : Increment minor version (1.2.3 → 1.3.0)"
            echo "   - 'major'  : Increment major version (1.2.3 → 2.0.0)"
            echo "   - Specific : Provide exact version (e.g., 1.2.4)"
            echo ""
            echo "💡 Examples:"
            echo "   bash scripts/release.sh patch"
            echo "   bash scripts/release.sh minor"
            echo "   bash scripts/release.sh 1.2.4"
            exit 1
            ;;
    esac

    NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
    print_info "Calculated new version: $NEW_VERSION"
fi

# Now run validation with version type
print_info "Running pre-release validation (strict mode)..."
echo ""

# Build validation command with strict mode by default
if [ "$SKIP_TESTS" = true ]; then
    VALIDATION_CMD="python3 scripts/validate_release.py --strict"
else
    VALIDATION_CMD="python3 scripts/validate_release.py --strict --run-tests"
fi

# Add version type if available
if [ -n "$VERSION_TYPE_ARG" ]; then
    VALIDATION_CMD="$VALIDATION_CMD --version-type $VERSION_TYPE_ARG"
    print_info "Validating for $VERSION_TYPE_ARG release"
fi

# Add new version for increment validation
VALIDATION_CMD="$VALIDATION_CMD --new-version $NEW_VERSION"
print_info "Validating version increment: $NEW_VERSION"
print_info "Semantic versioning enforcement: ENABLED"

if [ "$DRY_RUN" = false ]; then
    if ! $VALIDATION_CMD; then
        print_error "Validation failed!"
        echo ""
        echo "📍 The pre-release validation found issues that need to be fixed."
        echo "💡 Common fixes:"
        echo "   - Update CHANGELOG.md with release notes"
        echo "   - Commit uncommitted changes"
        echo "   - Ensure tests pass: pytest tests/"
        echo "   - Check version increment is correct"
        echo ""
        echo "For details, see the validation output above."
        echo ""
        if ! confirm "Continue anyway? (not recommended)"; then
            print_info "Release cancelled. Please fix issues and try again."
            exit 1
        fi
    fi
else
    print_dry_run "Run validation: $VALIDATION_CMD"
fi

# Confirm version
echo ""
print_warning "About to release version: v$NEW_VERSION"
print_warning "Current version: v$CURRENT_VERSION"
echo ""

if ! confirm "Is this correct?"; then
    print_info "Release cancelled"
    exit 0
fi

print_step "Step 3: Update CHANGELOG"

# Use Python changelog manager
CHANGELOG_CMD="python3 scripts/utils/changelog_manager.py release $NEW_VERSION"

if [ "$DRY_RUN" = true ]; then
    print_dry_run "Update CHANGELOG: $CHANGELOG_CMD"
else
    print_info "Running CHANGELOG manager..."
    if ! $CHANGELOG_CMD; then
        print_error "CHANGELOG update failed"
        exit 1
    fi
    save_state "changelog_updated" "$NEW_VERSION"
fi

# Show CHANGELOG preview
if [ "$DRY_RUN" = false ]; then
    echo ""
    print_info "CHANGELOG preview (first 15 lines of new version):"
    echo "---"
    python3 scripts/utils/changelog_manager.py get $NEW_VERSION 2>/dev/null | head -15 || echo "(Preview not available)"
    echo "---"
    echo ""
fi

if ! confirm "Proceed with committing changes?"; then
    print_info "Release cancelled. CHANGELOG has been updated but not committed."
    exit 0
fi

print_step "Step 4: Commit Changes"

# Commit CHANGELOG
COMMIT_MSG="chore: Release v$NEW_VERSION

- Update CHANGELOG.md with v$NEW_VERSION release notes
- Prepare for production release"

if [ "$DRY_RUN" = true ]; then
    print_dry_run "Stage files: git add CHANGELOG.md"
    print_dry_run "Commit: $COMMIT_MSG"
else
    print_info "Staging changes..."
    git add CHANGELOG.md

    print_info "Committing changes..."
    git commit -m "$COMMIT_MSG"
    print_success "Changes committed"
    save_state "committed" "$NEW_VERSION"
fi

print_step "Step 5: Merge dev to main"

if [ "$DRY_RUN" = true ]; then
    print_dry_run "Switch to main: git checkout main"
    print_dry_run "Merge dev: git merge dev"
else
    print_info "Switching to main branch..."
    git checkout main

    print_info "Merging dev into main..."
    if ! git merge dev; then
        save_state "merge_failed" "$NEW_VERSION,$(git rev-parse HEAD)"
        print_error "Merge failed!"
        echo ""
        echo "📍 Git encountered conflicts when merging dev into main."
        echo ""
        echo "💡 To resolve conflicts:"
        echo "  1. View conflicted files:"
        echo "     git status"
        echo ""
        echo "  2. Edit files to resolve conflicts (look for <<<<<<< markers)"
        echo ""
        echo "  3. Mark conflicts as resolved:"
        echo "     git add <resolved-files>"
        echo ""
        echo "  4. Complete the merge:"
        echo "     git commit"
        echo ""
        echo "  5. Resume release process:"
        echo "     git tag -a v$NEW_VERSION -m \"Release v$NEW_VERSION\""
        echo "     git push origin main v$NEW_VERSION"
        echo ""
        echo "  6. Or rollback:"
        echo "     bash scripts/release.sh --rollback"
        exit 1
    fi
    print_success "Merged dev to main"
    save_state "merged_to_main" "$NEW_VERSION"
fi

print_step "Step 6: Create and Push Version Tag"

TAG_MESSAGE="Release v$NEW_VERSION

$(python3 scripts/utils/changelog_manager.py get $NEW_VERSION 2>/dev/null | head -20 || echo "See CHANGELOG.md for details")"

if [ "$DRY_RUN" = true ]; then
    print_dry_run "Create tag: git tag -a v$NEW_VERSION -m \"...\""
    print_dry_run "Push main: git push origin main"
    print_dry_run "Push tag: git push origin v$NEW_VERSION"
    echo ""
    print_info "Tag message preview:"
    echo "$TAG_MESSAGE"
else
    print_info "Creating annotated tag v$NEW_VERSION..."
    git tag -a "v$NEW_VERSION" -m "$TAG_MESSAGE"
    save_state "tagged" "$NEW_VERSION,not_pushed"
    print_success "Created tag v$NEW_VERSION"

    print_info "Pushing main branch..."
    git push origin main
    print_success "Pushed main branch"

    print_info "Pushing tag v$NEW_VERSION..."
    git push origin "v$NEW_VERSION"
    save_state "tag_pushed" "$NEW_VERSION"
    print_success "Pushed tag v$NEW_VERSION"
fi

print_step "Step 7: Back to dev branch"

if [ "$DRY_RUN" = true ]; then
    print_dry_run "Switch to dev: git checkout dev"
    print_dry_run "Merge main: git merge main"
    print_dry_run "Push dev: git push origin dev"
else
    print_info "Switching back to dev branch..."
    git checkout dev

    print_info "Syncing dev with main..."
    git merge main
    git push origin dev
    print_success "Dev branch synced with main"
fi

print_step "Release Complete!"

# Clear state file on successful completion
if [ "$DRY_RUN" = false ]; then
    clear_state
fi

echo ""
print_success "Version v$NEW_VERSION release process completed!"
echo ""

if [ "$DRY_RUN" = true ]; then
    echo "This was a DRY-RUN. No actual changes were made."
    echo "Run without --dry-run to execute the release."
else
    echo "Next steps:"
    echo "  1. Monitor GitHub Actions: https://github.com/KaiTastic/pyASDReader/actions"
    echo "  2. PyPI workflow will publish to: https://pypi.org/project/pyASDReader/"
    echo "  3. GitHub Release will be created automatically"
    echo ""
    echo "Estimated workflow completion time:"
    echo "  - If tested on TestPyPI (within 7 days): 5-10 minutes"
    echo "  - If not tested on TestPyPI: 30-40 minutes (full test suite)"
    echo ""
    echo "Note: Times vary based on GitHub Actions load and PyPI availability"
    echo ""
    echo "Tip: Push to dev branch first to trigger TestPyPI testing."
fi
echo ""

#!/usr/bin/env bash
# Pre-push hard gate — enforces OpenSpec + CCPM + Epic + TDD before push.
# Called by PreToolUse hook in .claude/settings.json.
# Exit 0 = allow push, exit 1 = block and print what's missing.

set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

ERRORS=()

# ── 1. OpenSpec: no active changes (all archived) ───────────
ACTIVE=$(openspec list 2>/dev/null | grep -c "^  " || true)
if [ "$ACTIVE" -gt 0 ]; then
    ERRORS+=("❌ OpenSpec: $ACTIVE active change(s) not archived. Run: openspec archive <name> --yes")
fi

# ── 2. OpenSpec: archive has 4 artifacts for this branch ────
BRANCH=$(git branch --show-current)
PHASE_NUM=$(echo "$BRANCH" | grep -oP 'feature/\K\d+' || echo "")
if [ -n "$PHASE_NUM" ]; then
    ARCHIVE_DIR=$(ls -d openspec/changes/archive/*phase${PHASE_NUM}* 2>/dev/null | head -1 || echo "")
    if [ -n "$ARCHIVE_DIR" ]; then
        for artifact in proposal.md design.md tasks.md; do
            if [ ! -f "$ARCHIVE_DIR/$artifact" ]; then
                ERRORS+=("❌ OpenSpec: $ARCHIVE_DIR/$artifact missing")
            fi
        done
        if ! find "$ARCHIVE_DIR/specs" -name "*.md" 2>/dev/null | grep -q .; then
            ERRORS+=("❌ OpenSpec: $ARCHIVE_DIR/specs/ empty or missing")
        fi
    fi
fi

# ── 3. CCPM: issue-state exists and is completed ────────────
if [ -n "$PHASE_NUM" ]; then
    STATE_FILE=$(ls .claude/issue-state/${PHASE_NUM}-*.md 2>/dev/null | head -1 || echo "")
    if [ -z "$STATE_FILE" ]; then
        ERRORS+=("❌ CCPM: .claude/issue-state/${PHASE_NUM}-*.md not found")
    elif ! grep -q "status: completed" "$STATE_FILE"; then
        ERRORS+=("❌ CCPM: $STATE_FILE status is not 'completed'")
    fi
fi

# ── 4. Epic: Phase marked as completed ─────────────────────
EPIC_FILES=$(ls .claude/epics/*.md 2>/dev/null || echo "")
if [ -n "$EPIC_FILES" ] && [ -n "$PHASE_NUM" ]; then
    if ! grep -q "| ${PHASE_NUM}[a-z]*.*|.*✅" $EPIC_FILES 2>/dev/null; then
        ERRORS+=("❌ Epic: Phase $PHASE_NUM not marked ✅ in .claude/epics/")
    fi
fi

# ── 5. TDD: test commit before implementation commit ────────
BASE=$(git merge-base HEAD upstream/main 2>/dev/null || git merge-base HEAD origin/main 2>/dev/null || echo "")
if [ -n "$BASE" ]; then
    TEST_TS=$(git log --format="%at" "$BASE..HEAD" --diff-filter=A -- "tests/test_*.py" 2>/dev/null | tail -1 || echo "0")
    IMPL_TS=$(git log --format="%at" "$BASE..HEAD" --diff-filter=A -- ":!tests/" ":!openspec/" ":!.claude/" 2>/dev/null | tail -1 || echo "0")
    TEST_TS=${TEST_TS:-0}
    IMPL_TS=${IMPL_TS:-0}
    if [ "$IMPL_TS" != "0" ] && [ "$TEST_TS" != "0" ] && [ "$TEST_TS" -gt "$IMPL_TS" ] 2>/dev/null; then
        ERRORS+=("❌ TDD: test file committed after implementation (test=$TEST_TS, impl=$IMPL_TS)")
    fi
fi

# ── Report ──────────────────────────────────────────────────
if [ ${#ERRORS[@]} -gt 0 ]; then
    echo ""
    echo "╔══════════════════════════════════════════╗"
    echo "║  PUSH BLOCKED — 以下检查未通过           ║"
    echo "╚══════════════════════════════════════════╝"
    for err in "${ERRORS[@]}"; do
        echo "  $err"
    done
    echo ""
    echo "  修复上述问题后重新 push。"
    echo ""
    exit 1
fi

echo "✅ Pre-push gate: all checks passed"
exit 0

#!/usr/bin/env sh
# Smoke test for install.sh and the plotting skill. Uses only temporary folders.
#   sh tests/smoke_test.sh
# Set PUBSTYLE_ALLOW_STANDIN=1 on machines without Arial (draft font for the test).
set -eu

REPO="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd -P)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fail() { printf 'FAIL: %s\n' "$*"; exit 1; }
ok() { printf 'PASS: %s\n' "$*"; }

# 1. fresh project, all harnesses
P="$TMP/fresh"; mkdir -p "$P"
(cd "$P" && sh "$REPO/install.sh" >/dev/null)
[ -f "$P/.agents/skills/plotting/SKILL.md" ] || fail "fresh: skill not copied"
[ -L "$P/.claude/skills" ] && [ -f "$P/.claude/skills/plotting/SKILL.md" ] || fail "fresh: claude alias"
[ -f "$P/.qwen/skills/plotting/SKILL.md" ] || fail "fresh: qwen alias"
ok "fresh project install"

# 2. running again without --force changes nothing and does not fail
(cd "$P" && sh "$REPO/install.sh" | grep -q "skip:") || fail "rerun should skip"
ok "rerun skips existing install"

# 3. AI-Computational-Chemist-like layout: .claude/skills already links to .agents/skills
P="$TMP/aicc"; mkdir -p "$P/.agents/skills/vasp" "$P/.claude"
ln -s ../.agents/skills "$P/.claude/skills"
printf 'collection rules\n' > "$TMP/collection_AGENTS.md"
ln -s "$TMP/collection_AGENTS.md" "$P/AGENTS.md"
(cd "$P" && sh "$REPO/install.sh" --agents-md >/dev/null)
[ -f "$P/.claude/skills/plotting/SKILL.md" ] || fail "aicc: plotting not visible via existing link"
[ -d "$P/.agents/skills/vasp" ] || fail "aicc: existing skill touched"
grep -q Stormy-drawing "$TMP/collection_AGENTS.md" && fail "aicc: symlinked AGENTS.md was edited"
ok "side-by-side with an AI-Computational-Chemist layout"

# 4. existing real .claude/skills folder gets its own link
P="$TMP/realdir"; mkdir -p "$P/.claude/skills/other"
(cd "$P" && sh "$REPO/install.sh" --harness claude --agents-md >/dev/null)
[ -L "$P/.claude/skills/plotting" ] && [ -f "$P/.claude/skills/plotting/SKILL.md" ] || fail "realdir: link"
grep -q Stormy-drawing "$P/AGENTS.md" || fail "realdir: AGENTS.md note missing"
ok "existing harness folder and AGENTS.md note"

# 5. --global with a fake HOME, link mode
H="$TMP/home"; mkdir -p "$H"
HOME="$H" CODEX_HOME= sh "$REPO/install.sh" --global --harness claude,codex,agy --mode link >/dev/null
[ -L "$H/.claude/skills/plotting" ] && [ -f "$H/.codex/skills/plotting/SKILL.md" ] || fail "global link"
[ -f "$H/.gemini/config/skills/plotting/SKILL.md" ] || fail "global agy"
ok "global install, link mode"

# 6. --target and --dry-run
sh "$REPO/install.sh" --target "$TMP/custom" >/dev/null
[ -f "$TMP/custom/plotting/SKILL.md" ] || fail "target"
P="$TMP/dry"; mkdir -p "$P"
(cd "$P" && sh "$REPO/install.sh" --dry-run >/dev/null)
[ -z "$(ls -A "$P")" ] || fail "dry-run changed files"
ok "--target and --dry-run"

# 7. the installed skill works: new figure folder + all demo figure types
P="$TMP/fresh"
python3 "$P/.agents/skills/plotting/scripts/init_figure.py" "$P" Test_figure >/dev/null
[ -f "$P/figures/001_Test_figure/plot.py" ] && [ -f "$P/figures/_style/pubstyle.py" ] || fail "init_figure"
python3 "$P/.agents/skills/plotting/examples/demo_all_types.py" "$TMP/demo" > "$TMP/demo.log" 2>&1 \
  || { cat "$TMP/demo.log"; fail "demo_all_types"; }
grep -q "FAIL" "$TMP/demo.log" && { cat "$TMP/demo.log"; fail "a demo figure failed its checks"; }
[ "$(ls "$TMP/demo"/*.pdf | wc -l)" -eq 11 ] || fail "expected 11 demo figures"
ok "init_figure and all eleven demo figures"

printf 'smoke test: all passed\n'

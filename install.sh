#!/usr/bin/env sh
# Stormy-drawing installer: puts the `plotting` skill where AI agents look for skills.
set -eu

usage() {
  cat <<'USAGE'
Usage: /path/to/Stormy-drawing/install.sh [options]

Install the `plotting` skill for AI coding agents.

  Default (run inside a project directory)
      Copies the skill to ./.agents/skills/plotting and makes it visible to every
      harness in --harness (default: all):
        codex / kimi / pi / opencode / generic : .agents/skills/
        claude (Claude Code)                   : .claude/skills/
        qwen (Qwen Code)                       : .qwen/skills/
        zcode (ZCode)                          : .zcode/skills/ (project path unverified)
      A harness directory that does not exist yet becomes a link to .agents/skills
      (the same layout AI-Computational-Chemist uses, so both install side by side).
      A harness directory that already exists as a real folder gets its own link
      to .agents/skills/plotting.

  --global
      Installs into the user-level skill directory of each harness instead:
        claude ~/.claude/skills   codex $CODEX_HOME/skills (~/.codex/skills)
        qwen ~/.qwen/skills       zcode ~/.zcode/skills
        kimi / pi / opencode / generic ~/.agents/skills

Options:
  --harness LIST   Comma-separated: claude, codex, qwen, zcode, kimi, pi, opencode,
                   generic, or "all" (default).
  --global         Install for the current user instead of the current project.
  --target DIR     Install into DIR/plotting only (any other agent's skill folder).
  --mode copy|link copy (default): a fixed copy, so every project keeps the version
                   it was installed with. link: a symlink to this checkout, so
                   `git pull` here updates every install at once.
  --agents-md      Also add a short routing note to ./AGENTS.md telling agents to
                   use this skill for every figure (skipped if already present or if
                   AGENTS.md is a symlink, e.g. managed by AI-Computational-Chemist).
  --force          Replace an existing plotting skill.
  --dry-run        Print what would be done; change nothing.
  -h, --help       Show this help.

Examples:
  cd ~/projects/Li6PS5Cl_doping && ~/src/Stormy-drawing/install.sh
  ~/src/Stormy-drawing/install.sh --global --harness claude,codex
  ~/src/Stormy-drawing/install.sh --target ~/.config/some-agent/skills
USAGE
}

die() { printf 'ERROR: %s\n' "$*" >&2; exit 1; }

REPO_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)"
SKILL_SRC="$REPO_DIR/skills/plotting"
[ -f "$SKILL_SRC/SKILL.md" ] || die "cannot find skills/plotting/SKILL.md next to install.sh"

HARNESS="all"
GLOBAL=0
TARGET=""
MODE="copy"
AGENTS_MD=0
FORCE=0
DRY_RUN=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --harness) [ "$#" -ge 2 ] || die "--harness needs a list"; HARNESS="$2"; shift 2 ;;
    --global) GLOBAL=1; shift ;;
    --target) [ "$#" -ge 2 ] || die "--target needs a directory"; TARGET="$2"; shift 2 ;;
    --mode) [ "$#" -ge 2 ] || die "--mode needs copy or link"; MODE="$2"; shift 2 ;;
    --agents-md) AGENTS_MD=1; shift ;;
    --force) FORCE=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1 (see --help)" ;;
  esac
done

case "$MODE" in copy|link) ;; *) die "--mode must be copy or link" ;; esac
[ "$GLOBAL" -eq 1 ] && [ -n "$TARGET" ] && die "use either --global or --target, not both"

ALL_HARNESSES="claude codex qwen zcode kimi pi opencode generic"
if [ "$HARNESS" = "all" ]; then
  HARNESS_LIST="$ALL_HARNESSES"
else
  HARNESS_LIST="$(printf '%s' "$HARNESS" | tr ',' ' ' | sed 's/claudecode/claude/g')"
  for h in $HARNESS_LIST; do
    case " $ALL_HARNESSES " in *" $h "*) ;; *) die "unknown harness: $h" ;; esac
  done
fi
has() { case " $HARNESS_LIST " in *" $1 "*) return 0 ;; *) return 1 ;; esac; }

run() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '(dry-run) %s\n' "$*"
  else
    "$@"
  fi
}

# place_skill <skills_dir> : put plotting into <skills_dir>/plotting by copy or link
place_skill() {
  _dir="$1"
  _dest="$_dir/plotting"
  if [ -e "$_dest" ] || [ -L "$_dest" ]; then
    if [ "$FORCE" -eq 1 ]; then
      run rm -rf "$_dest"
    else
      printf 'skip: %s already exists (use --force to replace)\n' "$_dest"
      return 0
    fi
  fi
  [ -d "$_dir" ] || run mkdir -p "$_dir"
  if [ "$MODE" = "link" ]; then
    run ln -s "$SKILL_SRC" "$_dest"
  else
    run cp -R "$SKILL_SRC" "$_dest"
    run find "$_dest" -name __pycache__ -type d -prune -exec rm -rf {} +
  fi
  printf 'installed: %s (%s)\n' "$_dest" "$MODE"
}

# ---------------------------------------------------------------- --target
if [ -n "$TARGET" ]; then
  place_skill "$TARGET"
  exit 0
fi

# ---------------------------------------------------------------- --global
if [ "$GLOBAL" -eq 1 ]; then
  DONE=" "
  for h in $HARNESS_LIST; do
    case "$h" in
      claude) d="$HOME/.claude/skills" ;;
      codex) d="${CODEX_HOME:-$HOME/.codex}/skills" ;;
      qwen) d="$HOME/.qwen/skills" ;;
      zcode) d="$HOME/.zcode/skills" ;;
      *) d="$HOME/.agents/skills" ;;
    esac
    case "$DONE" in *" $d "*) continue ;; esac
    place_skill "$d"
    DONE="$DONE$d "
  done
  printf 'Next: restart or refresh your agent so it reloads its skills.\n'
  exit 0
fi

# ---------------------------------------------------------------- project (default)
PROJECT="$(pwd -P)"
[ "$PROJECT" = "$REPO_DIR" ] && die "run this from inside a project directory, not from the Stormy-drawing checkout (or use --global / --target)"

place_skill "$PROJECT/.agents/skills"

# alias_dir <harness dir relative to project, e.g. .claude/skills>
alias_dir() {
  _rel="$1"
  _abs="$PROJECT/$_rel"
  if [ -L "$_abs" ]; then
    if [ -e "$_abs/plotting" ]; then
      printf 'visible: %s/plotting (via existing link)\n' "$_rel"
    else
      printf 'NOTE: %s is a link that does not show plotting; add it there yourself or use --target\n' "$_rel"
    fi
  elif [ -d "$_abs" ]; then
    if [ -e "$_abs/plotting" ] || [ -L "$_abs/plotting" ]; then
      if [ "$FORCE" -eq 1 ]; then run rm -rf "$_abs/plotting"; else
        printf 'skip: %s/plotting already exists (use --force to replace)\n' "$_rel"; return 0; fi
    fi
    run ln -s "../../.agents/skills/plotting" "$_abs/plotting"
    printf 'linked: %s/plotting -> .agents/skills/plotting\n' "$_rel"
  else
    run mkdir -p "$(dirname "$_abs")"
    run ln -s "../.agents/skills" "$_abs"
    printf 'linked: %s -> .agents/skills\n' "$_rel"
  fi
}

has claude && alias_dir ".claude/skills"
has qwen && alias_dir ".qwen/skills"
has zcode && alias_dir ".zcode/skills"

if [ "$AGENTS_MD" -eq 1 ]; then
  f="$PROJECT/AGENTS.md"
  if [ -L "$f" ]; then
    printf 'NOTE: AGENTS.md is a symlink (probably AI-Computational-Chemist); not editing it.\n'
  elif [ -f "$f" ] && grep -q "Stormy-drawing" "$f"; then
    printf 'AGENTS.md already mentions Stormy-drawing; unchanged.\n'
  elif [ "$DRY_RUN" -eq 1 ]; then
    printf '(dry-run) append routing note to %s\n' "$f"
  else
    {
      [ -s "$f" ] && printf '\n'
      cat "$REPO_DIR/AGENTS_snippet.md"
    } >> "$f"
    printf 'updated: AGENTS.md (routing note for the plotting skill)\n'
  fi
fi

printf '\nDone. Figures go in ./figures/, one folder per figure; start one with:\n'
printf '  python .agents/skills/plotting/scripts/init_figure.py . <English_name>\n'
printf 'Next: restart or refresh your agent so it reloads its skills.\n'

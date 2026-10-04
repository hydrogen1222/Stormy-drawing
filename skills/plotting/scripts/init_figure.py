#!/usr/bin/env python3
"""Create a new figure folder inside a project, or bring the project's style
module up to date with this skill.

    python init_figure.py <project_root> <descriptive_english_name>
    python init_figure.py --update-style <project_root>

Example:
    python init_figure.py ~/projects/Li6PS5Cl_doping Li6PS5Cl_bulk_DOS
    -> figures/004_Li6PS5Cl_bulk_DOS/ with plot.py, README.md, archive/

On first use it also creates figures/_style/ with this project's copy of
pubstyle.py and an empty color registry colors.json. Both commands also check
that copy: if it is older than this skill's pubstyle.py (or has no version at
all), the old copy moves to figures/_style/archive/ and the new one replaces
it; figures drawn with the old copy must then be redrawn. colors.json is never
touched. Standard library only.
"""
import datetime
import re
import shutil
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent

try:  # Windows legacy code pages must not crash on non-ASCII paths
    sys.stdout.reconfigure(errors="backslashreplace")
except (AttributeError, ValueError):
    pass


def style_version(path: Path) -> tuple[int, ...]:
    """STYLE_VERSION of a pubstyle.py; (0, 0, 0) for copies made before versions existed."""
    m = re.search(r'^STYLE_VERSION = "([\d.]+)"', path.read_text(encoding="utf-8"), re.M)
    return tuple(int(x) for x in m.group(1).split(".")) if m else (0, 0, 0)


def sync_style(style: Path) -> None:
    """Create or update figures/_style/pubstyle.py from this skill."""
    src = SKILL / "scripts" / "pubstyle.py"
    dst = style / "pubstyle.py"
    style.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(src, dst)
        print(f"created {dst}")
        return
    new, old = style_version(src), style_version(dst)
    v = lambda t: ".".join(map(str, t)) if any(t) else "no version (before 0.4.0)"  # noqa: E731
    if old == new:
        print(f"style up to date: {dst} ({v(new)})")
    elif old > new:
        print(f"WARNING: {dst} ({v(old)}) is newer than this skill ({v(new)}); "
              "left unchanged. Update the installed skill instead.")
    else:
        archive = style / "archive"
        archive.mkdir(exist_ok=True)
        label = ".".join(map(str, old)) if any(old) else "unversioned"
        keep = archive / f"pubstyle_{label}_{datetime.date.today()}.py"
        shutil.move(str(dst), str(keep))
        shutil.copy2(src, dst)
        print(f"UPDATED {dst}: {v(old)} -> {v(new)} (old copy: {keep})")
        print("Figures drawn with the old style must be redrawn: run plot.py in each "
              "figure folder and check the new *_checks.txt.")


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--update-style":
        sync_style(Path(sys.argv[2]).expanduser().resolve() / "figures" / "_style")
        return 0
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    root = Path(sys.argv[1]).expanduser().resolve()
    name = sys.argv[2].strip()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]*", name):
        print("Name must be English letters, digits, _ . + - only (no spaces, no Chinese).")
        return 2
    if re.fullmatch(r"\d{3}_.*", name):
        print("Give the name without the number; the number is added automatically.")
        return 2

    figures = root / "figures"
    style = figures / "_style"
    sync_style(style)
    if not (style / "colors.json").exists():
        (style / "colors.json").write_text("{}\n", encoding="utf-8")
        print(f"created {style / 'colors.json'} (empty color registry)")

    numbers = [int(p.name[:3]) for p in figures.iterdir()
               if p.is_dir() and re.match(r"\d{3}_", p.name)]
    folder = figures / f"{(max(numbers) + 1 if numbers else 1):03d}_{name}"
    folder.mkdir()
    (folder / "archive").mkdir()
    for src, dst in (("plot_template.py", "plot.py"), ("README_template.md", "README.md")):
        text = (SKILL / "templates" / src).read_text(encoding="utf-8")
        (folder / dst).write_text(text.replace("__FIGURE_NAME__", folder.name), encoding="utf-8")
    print(f"created {folder}/ (plot.py, README.md, archive/)")
    print("next: copy the data file into it, fill README.md, edit plot.py, run it")
    return 0


if __name__ == "__main__":
    sys.exit(main())

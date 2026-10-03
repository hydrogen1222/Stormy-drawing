#!/usr/bin/env python3
"""Create a new figure folder inside a project.

    python init_figure.py <project_root> <descriptive_english_name>

Example:
    python init_figure.py ~/projects/Li6PS5Cl_doping Li6PS5Cl_bulk_DOS
    -> figures/004_Li6PS5Cl_bulk_DOS/ with plot.py, README.md, archive/

On first use it also creates figures/_style/ with this project's copy of
pubstyle.py and an empty color registry colors.json. Existing files are never
overwritten. Standard library only.
"""
import re
import shutil
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent


def main() -> int:
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
    style.mkdir(parents=True, exist_ok=True)
    if not (style / "pubstyle.py").exists():
        shutil.copy2(SKILL / "scripts" / "pubstyle.py", style / "pubstyle.py")
        print(f"created {style / 'pubstyle.py'}")
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

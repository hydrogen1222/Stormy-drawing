#!/usr/bin/env python3
"""Create a new figure folder inside a project, or bring the project's style
module up to date with this skill.

    python init_figure.py <project_root> <descriptive_english_name>
    python init_figure.py --update-style <project_root>

Example:
    python init_figure.py ~/projects/Li6PS5Cl_doping Li6PS5Cl_bulk_DOS
    -> figures/004_Li6PS5Cl_bulk_DOS/ with README.md, plot.py, data/, archive/
       (the first run of plot.py adds output/normal/ and output/soft/)

The project root must already exist (a mistyped path is an error, not a new
folder tree). On first use it also creates figures/_style/ with this project's copy of
pubstyle.py and pubparts.py (vector parts for image-editor layouts) and an empty
color registry colors.json. Both commands also check
that copy: if it is older than this skill's pubstyle.py (or has no version at
all), the old copy moves to figures/_style/archive/ and the new one replaces
it; figures drawn with the old copy must then be redrawn. colors.json is left
alone, except when the new style brings a new colour palette: then the old file
is archived next to the old pubstyle.py and a fresh registry starts (old figures
change colour when redrawn, and the archive lets you go back). Standard library
only.
"""
import datetime
import json
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


def palette_version(path: Path) -> int:
    m = re.search(r'^PALETTE_VERSION = (\d+)', path.read_text(encoding="utf-8"), re.M)
    return int(m.group(1)) if m else 1


def sync_palette(style: Path, src: Path) -> None:
    """A new colour palette needs a fresh colors.json; keep the old one in archive/."""
    reg = style / "colors.json"
    if not reg.exists():
        return
    try:
        stored = json.loads(reg.read_text(encoding="utf-8") or "{}")
    except ValueError:
        print(f"WARNING: {reg} is damaged and was left alone; restore it from archive/ "
              "or version control")
        return
    has_colors = any(isinstance(v, dict) and v for k, v in stored.items() if k != "_palette")
    old = stored.get("_palette", 1 if has_colors else None)
    new = palette_version(src)
    if old is None or old >= new:
        return
    archive = style / "archive"
    archive.mkdir(exist_ok=True)
    keep = archive / f"colors_palette{old}_{datetime.date.today()}.json"
    shutil.move(str(reg), str(keep))
    reg.write_text("{}\n", encoding="utf-8")
    print(f"NEW PALETTE ({old} -> {new}): colors.json archived to {keep}; the project starts "
          "with an empty registry, so each element gets its new color on the next redraw.")


def sync_style(style: Path) -> None:
    """Create or update figures/_style/ (pubstyle.py and pubparts.py) from this skill."""
    sync_pubstyle(style)
    sync_aux(style, "pubparts.py")


def sync_aux(style: Path, name: str) -> None:
    """Keep a helper module of the style folder identical to this skill's copy; a
    different older copy goes to archive/ first."""
    src, dst = SKILL / "scripts" / name, style / name
    if not dst.exists():
        shutil.copy2(src, dst)
        print(f"created {dst}")
    elif dst.read_bytes() != src.read_bytes():
        archive = style / "archive"
        archive.mkdir(exist_ok=True)
        stem = f"{Path(name).stem}_{datetime.date.today()}"
        keep, n = archive / f"{stem}.py", 2
        while keep.exists():
            keep = archive / f"{stem}_{n}.py"
            n += 1
        shutil.move(str(dst), str(keep))
        shutil.copy2(src, dst)
        print(f"UPDATED {dst} (old copy: {keep})")


def sync_pubstyle(style: Path) -> None:
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
        sync_palette(style, src)
        print(f"UPDATED {dst}: {v(old)} -> {v(new)} (old copy: {keep})")
        print("Figures drawn with the old style must be redrawn: run plot.py in each "
              "figure folder and check the new output/*/*_checks.txt.")


# names Windows refuses as folder names, whatever the extension
_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
             *(f"LPT{i}" for i in range(1, 10))}


def bad_name(name: str) -> str | None:
    """Why `name` cannot be a figure name, or None if it is fine."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.+-]*", name):
        return "Name must be English letters, digits, _ . + - only (no spaces, no Chinese)."
    if re.match(r"\d{3}(_|$)", name):
        return "Give the name without the number; the number is added automatically."
    if name.endswith("."):
        return "Name must not end with a dot (Windows cannot create such a folder)."
    if name.split(".")[0].upper() in _RESERVED:
        return f"'{name}' is a reserved device name on Windows; choose another name."
    return None


def project_root(arg: str) -> Path | None:
    """The project folder, which must exist. Prints the reason and returns None if not."""
    root = Path(arg).expanduser().resolve()
    if not root.is_dir():
        print(f"Project folder not found: {root}\n"
              "Check the path; nothing was created. (Create the folder yourself if it is new.)")
        return None
    return root


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--update-style":
        root = project_root(sys.argv[2])
        if root is None:
            return 2
        sync_style(root / "figures" / "_style")
        return 0
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    root = project_root(sys.argv[1])
    if root is None:
        return 2
    name = sys.argv[2].strip()
    problem = bad_name(name)
    if problem:
        print(problem)
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
    (folder / "data").mkdir()
    (folder / "archive").mkdir()
    for src, dst in (("plot_template.py", "plot.py"), ("README_template.md", "README.md")):
        text = (SKILL / "templates" / src).read_text(encoding="utf-8")
        (folder / dst).write_text(text.replace("__FIGURE_NAME__", folder.name), encoding="utf-8")
    print(f"created {folder}/ (plot.py, README.md, data/, archive/; output/ appears on the first run)")
    print("next: copy the data file into data/, fill README.md, edit plot.py, run it")
    return 0


if __name__ == "__main__":
    sys.exit(main())

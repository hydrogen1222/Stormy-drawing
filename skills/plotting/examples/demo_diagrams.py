#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy", "typst>=0.12"]
# ///
"""Draw the example diagrams of the plotting skill (examples/diagrams/*.typ).

    python demo_diagrams.py <output_dir>

Each example is placed in a throw-away project laid out like a real one
(<tmp>/_style/stormy.typ, <tmp>/<NN_name>/diagram.typ) and rendered with pubdiagram.render,
so the demo goes through the same path as a figure made with init_figure.py --diagram.
The contents are generic illustrations, not records of real calculations.

Layout of <output_dir>: one folder per diagram, holding its output/ (PNG and PDF for normal
and soft, checks.txt), plus _preview/ with every PNG side by side.
"""
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import pubdiagram as pd  # noqa: E402

EXAMPLES = [  # (file in examples/diagrams/, width)
    ("active_learning_loop.typ", "double"),
    ("message_passing_potential.typ", "single"),
    ("training_early_stopping.typ", "onehalf"),
]

root = Path(sys.argv[1] if len(sys.argv) > 1 else "demo_output") / "diagrams"
tmp = Path(tempfile.mkdtemp())
style = tmp / "_style"
style.mkdir()
for f in ("pubstyle.py", "pubdiagram.py", "stormy.typ"):
    shutil.copy2(SCRIPTS / f, style / f)
failed = []
for i, (src, width) in enumerate(EXAMPLES, 1):
    folder = tmp / f"{i:02d}_{Path(src).stem}"
    folder.mkdir()
    shutil.copy2(HERE / "diagrams" / src, folder / "diagram.typ")
    res = pd.render(folder, width)
    failed += [folder.name for r in res.values() for c in r if c.startswith("FAIL")]
if root.exists():
    shutil.rmtree(root)
shutil.copytree(tmp, root, ignore=shutil.ignore_patterns("_style", "archive", "__pycache__"))
shutil.rmtree(tmp)
print(f"diagrams written to {root}")
sys.exit(1 if failed else 0)

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy", "typst>=0.12"]
# ///
"""__FIGURE_NAME__

Diagram (flowchart, workflow, architecture). The drawing itself is diagram.typ in this folder
(Typst + fletcher, style figures/_style/stormy.typ); this script compiles and checks it.
Run in this folder:  uv run plot.py   (or: python plot.py)
For submission:      python plot.py --submit   (adds .svg, 1200-dpi .tif, transparent .png)
Live preview while editing: open diagram.typ in VS Code with the Tinymist extension.
What the diagram shows: README.md.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_style"))   # figures/_style/pubdiagram.py, stormy.typ
import pubdiagram as pd  # noqa: E402

# widest the diagram may be at print size: "single" (8.3 cm), "onehalf" (12 cm), "double" (17.4 cm)
WIDTH = "double"
# colour modes to draw. Both by default; the user picks one. Once they have, keep only
# that one here, e.g. MODES = ("soft",), and write the choice into README.md.
MODES = ("normal", "soft")

# writes output/<folder name>_<mode>.png and .pdf, output/checks.txt; without FAIL also
# copies the PNGs to figures/_preview/
pd.render(HERE, WIDTH, MODES)

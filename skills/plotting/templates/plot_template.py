#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy"]
# ///
"""__FIGURE_NAME__

Run in this folder:  uv run plot.py   (or: python plot.py)
For submission:      python plot.py --submit   (adds .svg, 1200-dpi .tif, transparent .png)
What the figure shows, where the data came from, and which column is which:
see README.md in this folder.
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_style"))   # figures/_style/pubstyle.py
import pubstyle as ps  # noqa: E402

# ---- EDIT HERE: replace every __PLACEHOLDER__ below (meaning of each: README.md)
SETTINGS = dict(
    data_file="__DATA_FILE__",         # file in THIS folder, copied from the calculation, never a path elsewhere
    x_meaning="__X_MEANING__",         # what column 1 is, with its unit (also write it in README.md)
    y_meaning="__Y_MEANING__",         # what column 2 is, with its unit
    series_key="__SERIES_KEY__",       # name for the color registry, e.g. "Li" or "Pristine"
    series_label="__SERIES_LABEL__",   # text in the legend
    x_label=r"__X_LABEL__",            # axis title, physical quantity (unit), e.g. r"Time (ps)"
    y_label=r"__Y_LABEL__",
)
_todo = [k for k, v in SETTINGS.items() if "__" in v]
if _todo:
    sys.exit("plot.py is still the template. Fill in " + ", ".join(_todo) +
             " at the top of this file (see README.md), then run it again.")

# colour modes to draw. Both by default; the user picks one. Once they have, keep only
# that one here, e.g. MODES = ("soft",), and write the choice into README.md.
MODES = ("normal", "soft")

# frame and tick marks: width and colour. Presets (pubstyle.AXIS_STYLES): "black_1.0pt" (default),
# "black_0.75pt", "black_1.5pt", "charcoal_1.0pt", "gray_0.75pt", "navy_1.0pt"; or your own, e.g.
# AXIS = dict(lw=1.2, color="#333333"). Text stays black. One axis style for every figure of a paper.
AXIS = "black_1.0pt"

# ---- data: files in data/ only, never paths into calculation folders
data = np.loadtxt(HERE / "data" / SETTINGS["data_file"], comments="#", encoding="utf-8")
x = data[:, 0]          # column 1
y = data[:, 1]          # column 2


def draw():
    """Build the figure; called once per colour mode."""
    reg = ps.ColorRegistry()
    fig, ax = ps.new_figure("standard")
    ax.plot(x, y, color=reg.color(SETTINGS["series_key"]), label=SETTINGS["series_label"])

    ax.set_xlim(x.min(), x.max())
    ps.nice_limits(ax, y.max())
    ax.set_xlabel(SETTINGS["x_label"])
    ax.set_ylabel(SETTINGS["y_label"])
    ps.place_legend(ax)             # remove for a single curve
    return fig


# writes output/<folder name>_<mode>.png and .pdf for every mode in MODES, plus output/checks.txt;
# a figure without FAIL is also copied to figures/_preview/
ps.save_modes(draw, HERE.name, HERE, MODES, axis=AXIS)

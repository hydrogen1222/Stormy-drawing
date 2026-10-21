#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy"]
# ///
"""__FIGURE_NAME__

Run in this folder:  uv run plot.py   (or: python plot.py)
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

ps.apply()
reg = ps.ColorRegistry()

# ---- data: files in this folder only, never paths into calculation folders
data = np.loadtxt(HERE / SETTINGS["data_file"], comments="#", encoding="utf-8")
x = data[:, 0]          # column 1
y = data[:, 1]          # column 2

# ---- plot
fig, ax = ps.new_figure("standard")
ax.plot(x, y, color=reg.color(SETTINGS["series_key"]), label=SETTINGS["series_label"])

ax.set_xlim(x.min(), x.max())
ps.nice_limits(ax, y.max())
ax.set_xlabel(SETTINGS["x_label"])
ax.set_ylabel(SETTINGS["y_label"])
ps.place_legend(ax)             # remove for a single curve

ps.save(fig, HERE.name, HERE)

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

ps.apply()
reg = ps.ColorRegistry()

# ---- data: files in this folder only, never paths into calculation folders
data = np.loadtxt(HERE / "__DATA_FILE__", comments="#")
x = data[:, 0]          # column 1: __X_MEANING__
y = data[:, 1]          # column 2: __Y_MEANING__

# ---- plot
fig, ax = ps.new_figure("standard")
ax.plot(x, y, color=reg.color("__SERIES_KEY__"), label="__SERIES_LABEL__")

ax.set_xlim(x.min(), x.max())
ps.nice_limits(ax, y.max())
ax.set_xlabel(r"__X_LABEL__")
ax.set_ylabel(r"__Y_LABEL__")
ps.place_legend(ax)             # remove for a single curve

ps.save(fig, HERE.name, HERE)

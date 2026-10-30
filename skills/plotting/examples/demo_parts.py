#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy"]
# ///
"""Draw every vector part of pubparts.py (colour bars, legends, axes triad, scale bar,
region strip, level diagram, inset, free-layout helpers) with made-up values.

    python demo_parts.py <output_dir>

Layout of <output_dir>, like demo_all_types.py: one folder per colour mode, one
folder per part inside it, e.g. normal/01_colorbar_vertical_esp/01_..._normal.pdf.
The values are invented; the parts only show what the functions make.
"""
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))
import pubstyle as ps  # noqa: E402
import pubparts as pp  # noqa: E402

root = Path(sys.argv[1] if len(sys.argv) > 1 else "demo_parts_output")


def view_matrix():
    """A made-up view: the rotation a VMD user would read with 'molinfo top get rotate_matrix'."""
    a, b = np.radians(35), np.radians(-20)
    rx = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    ry = np.array([[np.cos(b), 0, np.sin(b)], [0, 1, 0], [-np.sin(b), 0, np.cos(b)]])
    return rx @ ry


def free_layout():
    fig, ax = pp.new_part(5.0, 3.2)
    pp.arrow(ax, (0.5, 0.6), (1.9, 2.1))
    pp.label(ax, 0.5, 2.5, "Move up 0.6 Å")
    pp.dashed_box(ax, 2.6, 0.9, 1.6, 1.3)
    pp.dashed_circle(ax, 1.2, 1.0, 0.35)
    pp.dimension(ax, (0.4, 0.25), (4.6, 0.25), "4.20 Å")
    return fig


def inset_example():
    fig, ax = ps.new_figure()
    x = np.linspace(0, 10, 400)
    y = np.exp(-((x - 3) / 1.2) ** 2) + 0.35 * np.exp(-((x - 7) / 0.5) ** 2)
    ax.plot(x, y, color=ps.ColorRegistry(Path(tempfile.mkdtemp()) / "c.json").color("Li"))
    ax.set_xlim(0, 10)
    ps.nice_limits(ax, y.max())
    ax.set_xlabel(r"$E-E_{\rm F}$ (eV)")
    ax.set_ylabel("DOS (states/eV/f.u.)")
    iax = pp.add_inset(ax, (6.0, 8.0, 0.0, 0.4), (0.55, 0.45, 0.4, 0.4))
    iax.plot(x, y, color="0.15")
    return fig


def levels():
    return pp.level_diagram(
        [{"name": "Host", "levels": [(-6.1, "HOMO"), (-2.3, "LUMO")], "color": "Host"},
         {"name": "Doped", "levels": [(-5.4, "HOMO"), (-3.0, "Gap state"), (-2.2, "LUMO")]}],
        links=[(0, 0, 1, 0), (0, 1, 1, 2)])


PARTS = [
    ("01_colorbar_vertical_esp", lambda: pp.colorbar(-0.05, 0.05, "ESP (a.u.)")),
    ("02_colorbar_horizontal_esp", lambda: pp.colorbar(-41, 38, "ESP (kcal/mol)", orientation="horizontal", ticks=11, decimals=0, length_cm=8)),
    ("03_colorbar_posterized_reversed", lambda: pp.colorbar(0, 1, "ELF", bands=8, reverse=True)),
    ("03a_colorbar_bwr_esp", lambda: pp.colorbar(-0.05, 0.05, "ESP (a.u.)", cmap="bwr")),
    ("03b_nci_colorbar_iri", lambda: pp.nci_colorbar("iri")),
    ("03c_nci_colorbar_igmh", lambda: pp.nci_colorbar("igmh")),
    ("04_isosurface_legend_horizontal",
     lambda: pp.isosurface_legend([0.002, -0.002], unit=r"e $\rm\AA^{\rm -3}$", title="Isovalue")),
    ("05_isosurface_legend_vertical", lambda: pp.isosurface_legend([0.02, -0.02], orientation="vertical")),
    ("06_element_legend", lambda: pp.element_legend(["Li", "P", "S", "Cl"])),
    ("07_axes_triad_abc", lambda: pp.axes_triad(view_matrix(), labels=("a", "b", "c"))),
    ("08_scale_bar_5_angstrom", lambda: pp.scale_bar(5, "Å", 0.35)),
    ("09_region_strip_crystal_glass",
     lambda: pp.region_strip([("Crystal", 15), ("Glass", 15)], axis_label=r"$\zeta$ (Å)",
                             boundary_extra_cm=0.4)),
    ("10_level_diagram", levels),
    ("11_inset_zoom", inset_example),
    ("12_free_layout_helpers", free_layout),
]


def run(mode: str) -> None:
    ps.apply(mode=mode)
    for name, draw in PARTS:
        ps.save(draw(), f"{name}_{mode}", root / mode / name)


for mode in ps.MODES:
    run(mode)
ps.apply(mode="normal")

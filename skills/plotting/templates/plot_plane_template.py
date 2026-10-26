#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy"]
# ///
"""__FIGURE_NAME__

Scalar field (ELF, density, ...) on a plane exported from Multiwfn; atoms lying on the
plane are marked automatically. Run in this folder:  uv run plot.py   (or: python plot.py)
Needs two files in data/:
  plane.txt  Multiwfn main function 4, then "Export the current plane data to plane.txt"
  atoms.txt  one atom per line:  index element x y z   (Å, same index as in the molden file)
Which atoms define the plane, the grid and where the files came from: README.md.
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_style"))   # figures/_style/pubstyle.py (0.9.2 or newer)
import pubstyle as ps  # noqa: E402

# ---- settings (these are the only lines that ever need editing)
PLANE_FILE = "plane.txt"
ATOMS_FILE = "atoms.txt"
H_MAX = 0.4            # Å: atoms closer than this to the plane are marked
ORIGIN_ATOM = None     # e.g. "O337": put (0, 0) on that atom so the axes read as distances
                       # from it; None keeps Multiwfn's grid corner as (0, 0)
VMIN, VMAX = 0.0, 1.0  # ELF is always 0-1; change only for another quantity (and the cmap)
CMAP = "turbo"
IMAGE_PX = 1500        # pixels along the longer side of the picture kept in PDF/SVG/TIFF (see below)
MODES = ("normal", "soft")   # once the user has chosen, keep only that one (see README.md)

for name in (PLANE_FILE, ATOMS_FILE):
    if not (HERE / "data" / name).exists():
        sys.exit(f"data/{name} is missing: copy it into this folder's data/ (see the top of this file).")

m = ps.read_plane(HERE / "data" / PLANE_FILE)
atoms = []
for line in (HERE / "data" / ATOMS_FILE).read_text(encoding="utf-8").splitlines():
    t = line.split()
    if len(t) >= 5:
        atoms.append((t[0], t[1], *map(float, t[2:5])))
if not atoms:
    sys.exit(f"data/{ATOMS_FILE}: no lines of the form 'index element x y z'.")
u, v, h = m.project([a[2:] for a in atoms])

du = dv = 0.0
if ORIGIN_ATOM:
    ref = [i for i, a in enumerate(atoms) if f"{a[1]}{a[0]}" == ORIGIN_ATOM]
    if not ref:
        sys.exit(f"ORIGIN_ATOM {ORIGIN_ATOM!r} is not in data/{ATOMS_FILE} (write it as element+index, e.g. O337).")
    du, dv = u[ref[0]], v[ref[0]]
u, v = u - du, v - dv
extent = (m.u[0] - du, m.u[-1] - du, m.v[0] - dv, m.v[-1] - dv)
inside = (u >= extent[0]) & (u <= extent[1]) & (v >= extent[2]) & (v <= extent[3]) & (h <= H_MAX)
shown = [(a[1], a[0], uu, vv) for a, uu, vv, ok in zip(atoms, u, v, inside) if ok]
print(f"{len(shown)} atoms within {H_MAX} Å of the plane:", ", ".join(f"{el}{n}" for el, n, _, _ in shown))
print(f"grid {m.Z.shape[1]} x {m.Z.shape[0]}, {extent[1] - extent[0]:.2f} x {extent[3] - extent[2]:.2f} Å, "
      f"value range {m.Z.min():.3f} to {m.Z.max():.3f}")


def resample(Z, n):
    """Z on an n-pixel grid along its longer side (linear interpolation, aspect kept).

    Why: with interpolation="bilinear" matplotlib resamples the picture to 100 pixels per
    inch before writing PDF/SVG, so a 200 x 200 or a 4000 x 4000 grid both end up as the
    same ~170-pixel blur when zoomed. Resampling here and drawing with interpolation="none"
    keeps all n pixels in the vector files, whatever the density of plane.txt."""
    nv, nu = Z.shape
    k = n / max(nu, nv)
    xu = np.linspace(0, nu - 1, max(2, round(nu * k)))
    xv = np.linspace(0, nv - 1, max(2, round(nv * k)))
    A = np.array([np.interp(xu, np.arange(nu), row) for row in Z])
    return np.array([np.interp(xv, np.arange(nv), col) for col in A.T]).T


Zdraw = resample(m.Z, IMAGE_PX)


def draw():
    """Build the figure; called once per colour mode."""
    reg = ps.ColorRegistry()
    fig, ax = ps.new_figure(colorbar=True)
    im = ax.imshow(Zdraw, origin="lower", extent=extent, cmap=CMAP, vmin=VMIN, vmax=VMAX,
                   interpolation="none")
    for el, n, uu, vv in shown:
        ax.plot(uu, vv, "o", color=reg.color(el), mec="white", mew=0.8, ms=5)
        ps.label_point(ax, uu, vv, f"{el}{n}")
    ax.set_aspect("equal")
    ax.set_xlabel(r"$u$ (Å)")
    ax.set_ylabel(r"$v$ (Å)")
    ps.add_colorbar(fig, ax, im, "ELF")
    return fig


ps.save_modes(draw, HERE.name, HERE, MODES)

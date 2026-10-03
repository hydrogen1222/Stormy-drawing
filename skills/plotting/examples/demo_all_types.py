#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy"]
# ///
"""Draw every figure type of the plotting skill from SYNTHETIC data.

    python demo_all_types.py <output_dir>

All curves are made up (sums of Gaussians and the like). They only show the
style and test pubstyle.py; they are not calculation results and must never be
used as such. Each figure carries "synthetic data" in its file name.
"""
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import pubstyle as ps  # noqa: E402

out = Path(sys.argv[1] if len(sys.argv) > 1 else "demo_output")
out.mkdir(parents=True, exist_ok=True)
ps.apply()
reg = ps.ColorRegistry(Path(tempfile.mkdtemp()) / "colors.json")
g = lambda x, c, w, a: a * np.exp(-((x - c) / w) ** 2)  # noqa: E731

# ---------------------------------------------------------------- DOS
e = np.linspace(-6, 6, 1500)
edge = 1 / (1 + np.exp(e / 0.08)) + 1 / (1 + np.exp(-(e - 3.0) / 0.08))
pdos = {"S": g(e, -1.0, 0.8, 2.2) + g(e, -3.2, 0.7, 1.2) + g(e, 4.2, 0.9, 0.5),
        "Cl": g(e, -2.0, 0.5, 0.9),
        "P": g(e, -4.6, 0.5, 0.8) + g(e, 4.6, 0.8, 0.6),
        "Li": g(e, -3.0, 1.2, 0.15) + g(e, 4.8, 1.0, 0.4)}
pdos = {k: v * edge for k, v in pdos.items()}
total = sum(pdos.values()) * 1.1
fig, ax = ps.new_figure()
ax.fill_between(e, total, color="0.85", lw=0, label="Total", zorder=0.8)
for el, y in pdos.items():
    ps.gradient_fill(ax, e, y, reg.color(el))
    ax.plot(e, y, color=reg.color(el), label=el, zorder=2)
ax.axvline(0, **ps.REFERENCE_LINE)
ax.set_xlim(-6, 6)
ax.xaxis.set_major_locator(ps.mpl.ticker.MultipleLocator(2))
ps.nice_limits(ax, total.max())
ps.gap_arrow(ax, 0.0, 3.0, y=0.35)
ax.set_xlabel(r"$E-E_{\rm VBM}$ (eV)")
ax.set_ylabel("DOS (states/eV/f.u.)")
ps.place_legend(ax)
ps.save(fig, "01_dos_synthetic_data", out)

# ---------------------------------------------------------------- bands + strip
k = np.linspace(0, 3, 300)
kt, kl = [0, 1, 1.8, 3], [r"$\rm\Gamma$", "X", "W|K", r"$\rm\Gamma$"]
fig, ax = ps.new_figure("tall")
for n in range(4):
    ax.plot(k, -0.9 * n - 0.6 * np.sin(np.pi * k * (n + 1) / 3) ** 2, color="0.15", lw=1.2)
for n in range(3):
    ax.plot(k, 3.0 + 0.8 * n + 0.7 * np.sin(np.pi * k / 3 * (n + 1)) ** 2, color="0.15", lw=1.2)
for x in kt[1:-1]:
    ax.axvline(x, color="0.6", lw=0.8)
ax.axhline(0, **ps.REFERENCE_LINE)
ax.plot([0], [0.0], "o", color=ps.CATEGORICAL[1], ms=5, clip_on=False, zorder=3)
ax.plot([0], [3.0], "o", color=ps.CATEGORICAL[0], ms=5, clip_on=False, zorder=3)
ps.gap_arrow(ax, 0.0, 3.0, y=0.15, vertical=True, text_fmt="{:.2f} eV (direct)")
ax.set_xlim(0, 3)
ax.set_xticks(kt, kl)
ax.xaxis.set_minor_locator(ps.mpl.ticker.NullLocator())
ax.set_ylim(-4, 6)
ax.yaxis.set_major_locator(ps.mpl.ticker.MultipleLocator(2))
ax.set_ylabel(r"$E-E_{\rm VBM}$ (eV)")
ps.save(fig, "02a_bands_synthetic_data", out)

fig, ax = ps.new_figure("strip")
ee = np.linspace(-4, 6, 800)
dd = (g(ee, -1.0, 0.8, 2.2) + g(ee, -3.0, 0.7, 1.2)) * (ee < 0) + g(ee, 4.2, 0.9, 0.8) * (ee > 3)
ax.fill_betweenx(ee, dd, color=reg.color("S"), alpha=0.25, lw=0)
ax.plot(dd, ee, color=reg.color("S"))
ax.axhline(0, **ps.REFERENCE_LINE)
ax.set_ylim(-4, 6)
ax.set_xlim(0, 2.5)
ax.tick_params(labelleft=False)
ax.set_xticks([])
ax.xaxis.set_minor_locator(ps.mpl.ticker.NullLocator())
ax.set_xlabel("DOS")
ps.save(fig, "02b_dos_strip_synthetic_data", out)

# ---------------------------------------------------------------- NEB
dist = np.linspace(0, 3.6, 9)
en = 0.30 * np.sin(np.pi * dist / 3.6) ** 2 * (1 + 0.15 * np.sin(2 * np.pi * dist / 3.6))
fine = np.linspace(0, 3.6, 300)
ef = 0.30 * np.sin(np.pi * fine / 3.6) ** 2 * (1 + 0.15 * np.sin(2 * np.pi * fine / 3.6))
climb = True   # in real use: ps.incar_true(HERE / "INCAR", "LCLIMB")
c = reg.color("Li path A", "structure")
fig, ax = ps.new_figure()
ax.plot(fine, ef, color=c, zorder=1)
ax.plot(dist, en, "o", color=c, mfc="white", zorder=2)
i = int(np.argmax(en))
if climb:
    ax.plot(dist[i], en[i], "o", color=c, zorder=3)
ax.annotate(f"{en[i]:.2f} eV", xy=(dist[i], en[i]), xytext=(0, 8), textcoords="offset points", ha="center")
ax.set_xlim(-0.15, 3.75)
ps.nice_limits(ax, en.max(), headroom=0.25, pad_low=0.25)
ax.set_xlabel("Migration distance (Å)")
ax.set_ylabel("Relative energy (eV)")
ps.save(fig, "03_neb_barrier_synthetic_data", out)

# ---------------------------------------------------------------- RDF
r = np.linspace(1.5, 5.0, 600)
fig, ax = ps.new_figure()
curves = {"Li-S": g(r, 2.45, 0.12, 6.0) + g(r, 4.0, 0.4, 1.2) + 1 - np.exp(-((r - 1.5) / 1.2) ** 4),
          "Li-Cl": g(r, 2.60, 0.15, 3.5) + g(r, 4.3, 0.5, 0.9) + 1 - np.exp(-((r - 1.5) / 1.4) ** 4)}
for pair, y in curves.items():
    ax.plot(r, y, color=reg.color(pair, "pair"), label=pair.replace("-", "–"))
ax.set_xlim(1.5, 5.0)
ps.nice_limits(ax, max(y.max() for y in curves.values()))
ax.set_xlabel(r"$r$ (Å)")
ax.set_ylabel(r"$g(r)$")
ps.place_legend(ax)
ps.save(fig, "04_rdf_synthetic_data", out)

# ---------------------------------------------------------------- MSD
t = np.linspace(0, 50, 400)
temps = [600, 700, 800, 900, 1000]
fig, ax = ps.new_figure()
ymax = 0
for T, col in reversed(list(zip(temps, ps.ordered_colors(len(temps))))):
    D = 0.02 * np.exp(-0.25 / 8.617e-5 * (1 / T - 1 / 1000))
    y = 6 * D * t + 0.8 * (1 - np.exp(-t / 0.5))
    ax.plot(t, y, color=col, label=f"{T} K")
    ymax = max(ymax, y.max())
ax.axvspan(5, 40, color="0.92", zorder=0, lw=0)
ax.set_xlim(0, 50)
ps.nice_limits(ax, ymax)
ax.set_xlabel("Time (ps)")
ax.set_ylabel(r"Li MSD (${\rm \AA}^{\rm 2}$)")
ps.place_legend(ax)
ps.save(fig, "05_msd_synthetic_data", out)

# ---------------------------------------------------------------- Arrhenius
invT = np.array([1.0, 1.111, 1.25, 1.429, 1.667])
logD = -4.2 - 1.26 * (invT - 1.0) + np.array([0.03, -0.02, 0.02, -0.03, 0.01])
(slope, icpt), cov = np.polyfit(invT, logD, 1, cov=True)
ea = -slope * 8.617e-5 * 1000 * np.log(10)
ea_err = np.sqrt(cov[0, 0]) * 8.617e-5 * 1000 * np.log(10)
fig, ax = ps.new_figure(top_axis=True)
xx = np.linspace(0.9, 3.45, 50)
ax.plot(xx, slope * xx + icpt, color=reg.color("Linear fit", "series"), lw=1.2, ls="--", label="Linear fit")
ax.plot(invT, logD, "o", color=reg.color("MD", "series"), mfc="white", label="MD")
ax.plot([1000 / 300], [slope * 1000 / 300 + icpt], "D", color=reg.color("MD", "series"), label="Extrapolated, 300 K")
ax.text(0.05, 0.08, rf"$E_{{\rm a}}$ = {ea:.2f} ± {ea_err:.2f} eV", transform=ax.transAxes)
ax.set_xlim(0.9, 3.5)
ps.nice_limits(ax, -3.9, data_min=-7.6, start_at_zero=False, headroom=0.0)
ax.set_xlabel(r"1000/$T$ (K$^{\rm {-}1}$)")
ax.set_ylabel(r"log$_{\rm 10}$($D$/cm$^{\rm 2}$ s$^{\rm {-}1}$)")
top = ax.secondary_xaxis("top", functions=(lambda x: 1000 / np.maximum(x, 1e-6),
                                           lambda T: 1000 / np.maximum(T, 1e-6)))
top.set_xticks([1000, 600, 400, 300])
top.minorticks_off()
top.set_xlabel(r"$T$ (K)")
ps.place_legend(ax)
ps.save(fig, "06_arrhenius_synthetic_data", out)

# ---------------------------------------------------------------- 2D map
x = np.linspace(0, 8, 200)
X, Y = np.meshgrid(x, np.linspace(0, 6, 150))
Z = (g(X, 2.5, 0.6, 1) * g(Y, 3, 0.6, 1) - g(X, 5.5, 0.8, 0.8) * g(Y, 3, 0.8, 1)
     + 0.3 * g(X, 4, 0.4, 1) * g(Y, 1.5, 0.4, 1))
a = np.abs(Z).max()
fig, ax = ps.new_figure(colorbar=True)
im = ax.imshow(Z, extent=(0, 8, 0, 6), origin="lower", cmap=ps.DIVERGING, vmin=-a, vmax=a)
ax.plot([2.5, 5.5], [3, 3], "o", color=reg.color("S"), mec="0.1", mew=0.6, ms=5)
ax.set_aspect("equal")
ax.set_xlabel(r"$x$ (Å)")
ax.set_ylabel(r"$y$ (Å)")
ps.add_colorbar(fig, ax, im, r"$\Delta\rho$ (e/${\rm \AA}^{\rm 3}$)")
ps.save(fig, "07_charge_difference_map_synthetic_data", out)

# ---------------------------------------------------------------- bars
names = ["Pristine", "Br-doped", "O-doped"]
vals = np.array([0.31, 0.24, 0.38])
err = np.array([0.02, 0.03, 0.02])
fig, ax = ps.new_figure()
xs = np.arange(len(names))
ax.bar(xs, vals, width=0.6, color=[reg.color(n, "structure") for n in names], edgecolor="0.2", lw=0.8,
       yerr=err, capsize=3, error_kw=dict(lw=1.0))
for xi, v, er in zip(xs, vals, err):
    ax.text(xi, v + er + 0.01, f"{v:.2f}", ha="center", va="bottom")
ax.set_xticks(xs, names)
ax.xaxis.set_minor_locator(ps.mpl.ticker.NullLocator())
ax.set_xlim(-0.6, len(names) - 0.4)
ps.nice_limits(ax, (vals + err).max(), headroom=0.2)
ax.set_ylabel("Barrier (eV)")
ps.save(fig, "08_bars_synthetic_data", out)

# ---------------------------------------------------------------- the check must catch this
fig, ax = ps.new_figure()
ax.plot([0, 1], [0, 1], color=reg.color("S"))
ax.set_ylabel("Area (cm²)")
checks = ps.check_figure(fig)
assert any(c.startswith("FAIL text") for c in checks), "Unicode superscript was not caught"
ps.plt.close(fig)
print("self-test: Unicode superscript correctly rejected")

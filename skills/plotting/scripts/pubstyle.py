"""Shared figure style for Stormy's projects (the `plotting` skill).

One copy of this file lives in each project at figures/_style/pubstyle.py
(made by init_figure.py). Every figure's plot.py imports it, so changing the
style here changes every figure of that project on the next redraw.

Typical plot.py:

    import pubstyle as ps
    ps.apply()
    reg = ps.ColorRegistry()                  # figures/_style/colors.json
    fig, ax = ps.new_figure("standard")       # 8 cm x 6 cm
    ax.plot(x, y, color=reg.color("Li"), label="Li")
    ps.nice_limits(ax, y.max())               # axis top: max + 10 %, rounded up
    ps.place_legend(ax)                       # top right unless it covers data
    ps.save(fig, "003_Li6PS5Cl_bulk_DOS")     # PNG x2, PDF, SVG + checks

Everything here follows the decisions recorded in the skill's SKILL.md.
"""
from __future__ import annotations

import json
import logging
import math
import os
import re
from pathlib import Path

import numpy as np
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, to_hex, to_rgb  # noqa: E402
from matplotlib.text import Text  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

CM = 1 / 2.54
STYLE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------- fonts

FONT = "Arial"
# Liberation Sans has exactly Arial's letter widths. It is allowed ONLY for
# drafts, and only when PUBSTYLE_ALLOW_STANDIN=1 is set; save() then marks the
# figure as a draft in its check report.
STANDIN_FONT = "Liberation Sans"


def _pick_font() -> tuple[str, bool]:
    names = {f.name for f in font_manager.fontManager.ttflist}
    if FONT in names:
        return FONT, False
    if os.environ.get("PUBSTYLE_ALLOW_STANDIN") == "1" and STANDIN_FONT in names:
        return STANDIN_FONT, True
    raise RuntimeError(
        "Arial is not installed on this machine. Follow references/setup.md "
        "(copy arial.ttf, arialbd.ttf, ariali.ttf, arialbi.ttf to "
        "~/.local/share/fonts/ and delete ~/.cache/matplotlib). "
        "Do not switch to another font."
    )


# ---------------------------------------------------------------- sizes

# width, height in cm
CANVAS_CM = {"standard": (8.0, 6.0), "tall": (6.0, 8.0), "strip": (3.0, 8.0)}

# Fixed frame position inside each canvas (left, bottom, right, top margins in
# cm). Every figure of one canvas type has its frame at exactly the same place,
# so panels line up when Stormy assembles them in GIMP.
MARGINS_CM = {
    "standard": (1.55, 1.25, 0.35, 0.35),
    "tall": (1.55, 1.25, 0.35, 0.35),
    "strip": (0.25, 1.25, 0.25, 0.35),   # y axis shared with the band plot
}

FONT_PT = 10
LEGEND_PT = 9
DATA_LW = 1.5
FRAME_LW = 1.2
MAJOR_LEN = 4.0
MINOR_LEN = 2.2
MARKER_SIZE = 6.0

# ---------------------------------------------------------------- colors

# Unordered categories (elements, structures, methods). Soft tones; this order
# passes the colorblind adjacent-pair check. Never generate a 7th color: use
# line styles or marker shapes, or split the figure.
CATEGORICAL = ["#C8553D", "#3D6FB6", "#C98A1E", "#2A9D8F", "#6B5BA8", "#D0628E"]

# Ordered quantities (temperature, concentration, strain): light to dark.
# "warm" is the default; "cool" only for a second ordered quantity.
RAMPS = {
    "warm": ["#F2B66D", "#E07B53", "#C24E6A", "#7E3A80", "#3B2D6B"],
    "cool": ["#9AD0C2", "#4FA3A5", "#3A7AA8", "#3F4F98", "#2D2560"],
}

# Signed quantities (charge density difference): blue - white - red.
DIVERGING = LinearSegmentedColormap.from_list(
    "signed", ["#2D4F8F", "#7FA6D6", "#FFFFFF", "#E39A7F", "#A8322A"])

REFERENCE_LINE = dict(color="0.45", lw=1.0, ls="--", zorder=0.5)


def ordered_colors(n: int, ramp: str = "warm") -> list[str]:
    """n colors from light to dark. Low value = light, high value = dark."""
    cmap = LinearSegmentedColormap.from_list(ramp, RAMPS[ramp])
    if n == 1:
        return [to_hex(cmap(0.7))]
    return [to_hex(cmap(x)) for x in np.linspace(0.08, 1.0, n)]


def sequential_cmap(ramp: str = "cool", light: str = "#FFFFFF"):
    """Colormap for non-negative 2D maps: white (zero) to the ramp's dark end."""
    return LinearSegmentedColormap.from_list(f"{ramp}_seq", [light] + RAMPS[ramp][1:])


# Familiar hues for common elements, used when still free in that group.
# Only a preference: any other element simply gets the next free color.
PREFERRED = {"S": "#C98A1E", "Cl": "#2A9D8F", "P": "#6B5BA8", "Li": "#3D6FB6",
             "O": "#C8553D", "Na": "#D0628E", "Br": "#C8553D"}

GROUPS = ("element", "pair", "structure", "series")


class ColorRegistry:
    """Project-wide fixed colors, stored in figures/_style/colors.json.

    Colors are kept per group, so each group has the full six colors:
      element    Li, S, Br ...           (also used by structure figures)
      pair       Li-S, Li-Cl ...         (RDF and the like)
      structure  pristine, Br-doped, path A ...
      series     anything else (fit vs data, methods)
    A key gets a color the first time it is asked for and keeps it forever.
    Nothing is pre-assigned, so doped or new elements are handled the same way.
    """

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else STYLE_DIR / "colors.json"
        self.data = {g: {} for g in GROUPS}
        if self.path.exists():
            stored = json.loads(self.path.read_text(encoding="utf-8") or "{}")
            for g, d in stored.items():
                self.data.setdefault(g, {}).update(d)

    def color(self, key: str, group: str = "element") -> str:
        if group not in GROUPS:
            raise ValueError(f"group must be one of {GROUPS}")
        table = self.data[group]
        if key in table:
            return table[key]
        used = set(table.values())
        free = [c for c in CATEGORICAL if c not in used]
        if not free:
            raise RuntimeError(
                f"All {len(CATEGORICAL)} colors of group '{group}' are taken; cannot add "
                f"'{key}'. Distinguish further series by line style or marker, or split "
                "the figure. Do not invent a new color.")
        pick = PREFERRED.get(key) if group == "element" else None
        chosen = pick if pick in free else free[0]
        table[key] = chosen
        self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False) + "\n",
                             encoding="utf-8")
        print(f"color registry: {group} '{key}' -> {chosen} (new, recorded in {self.path})")
        return chosen


# ---------------------------------------------------------------- style

_STATE = {"font": None, "standin": False}


def apply() -> None:
    font, standin = _pick_font()
    _STATE.update(font=font, standin=standin)
    mpl.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": [font],
        "font.weight": "bold", "axes.labelweight": "bold",
        "font.size": FONT_PT, "axes.labelsize": FONT_PT, "axes.titlesize": FONT_PT,
        "xtick.labelsize": FONT_PT, "ytick.labelsize": FONT_PT,
        "legend.fontsize": LEGEND_PT,
        # math: symbols bold italic, \rm{...} bold upright, all in the same font
        "mathtext.fontset": "custom", "mathtext.default": "it",
        "mathtext.rm": f"{font}:bold", "mathtext.bf": f"{font}:bold",
        "mathtext.it": f"{font}:italic:bold", "mathtext.sf": f"{font}:bold",
        "mathtext.cal": f"{font}:bold",
        # Origin-like: closed frame, ticks out, major + minor, left/bottom only
        "axes.linewidth": FRAME_LW, "axes.grid": False,
        "xtick.direction": "out", "ytick.direction": "out",
        "xtick.top": False, "ytick.right": False,
        "xtick.major.size": MAJOR_LEN, "ytick.major.size": MAJOR_LEN,
        "xtick.minor.size": MINOR_LEN, "ytick.minor.size": MINOR_LEN,
        "xtick.major.width": FRAME_LW, "ytick.major.width": FRAME_LW,
        "xtick.minor.width": FRAME_LW * 0.8, "ytick.minor.width": FRAME_LW * 0.8,
        "xtick.minor.visible": True, "ytick.minor.visible": True,
        "lines.linewidth": DATA_LW, "lines.markersize": MARKER_SIZE,
        "lines.markeredgewidth": DATA_LW,
        "legend.frameon": False, "legend.handlelength": 1.6,
        "legend.borderaxespad": 0.4,
        "axes.unicode_minus": True, "axes.formatter.useoffset": False,
        "axes.formatter.limits": (-4, 5),
        "pdf.fonttype": 42, "svg.fonttype": "none",   # text stays editable
        "savefig.facecolor": "white",
    })


TOP_AXIS_EXTRA_CM = 0.9     # room for a second (top) axis, Arrhenius plots
COLORBAR_EXTRA_CM = 1.8     # room for a colorbar on the right, 2D maps


def new_figure(canvas: str = "standard", top_axis: bool = False, colorbar: bool = False):
    """One panel on a fixed-size canvas with a fixed frame position.
    top_axis / colorbar reserve fixed extra room (same for every such figure)."""
    if _STATE["font"] is None:
        apply()
    w, h = CANVAS_CM[canvas]
    left, bottom, right, top = MARGINS_CM[canvas]
    top += TOP_AXIS_EXTRA_CM if top_axis else 0.0
    right += COLORBAR_EXTRA_CM if colorbar else 0.0
    fig = plt.figure(figsize=(w * CM, h * CM))
    ax = fig.add_axes((left / w, bottom / h, 1 - (left + right) / w, 1 - (bottom + top) / h))
    ax.xaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    fig._pubstyle_canvas = canvas
    return fig, ax


def add_colorbar(fig, ax, mappable, label: str):
    """Colorbar in the space reserved by new_figure(colorbar=True), same height
    as the frame, with outward ticks like the main axes."""
    ax.apply_aspect()
    pos = ax.get_position()
    w_fig = fig.get_figwidth() / CM
    cax = fig.add_axes((pos.x1 + 0.25 / w_fig, pos.y0, 0.3 / w_fig, pos.height))
    cb = fig.colorbar(mappable, cax=cax)
    cb.set_label(label)
    cb.outline.set_linewidth(FRAME_LW)
    cb.ax.tick_params(direction="out", width=FRAME_LW, length=MAJOR_LEN)
    cb.ax.minorticks_off()
    return cb


# ---------------------------------------------------------------- axis limits

def _nice_step(span: float, max_ticks: int = 6) -> float:
    raw = span / (max_ticks - 1)
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if m * mag >= raw - 1e-12:
            return m * mag
    return 10 * mag


def nice_limits(ax, data_max: float, data_min: float = 0.0, axis: str = "y",
                headroom: float = 0.10, start_at_zero: bool = True,
                pad_low: float = 0.0, max_ticks: int = 6):
    """Axis end = data max + headroom, rounded up to a labeled major tick.

    Example: peak 50 -> 0 to 60, labels every 20. Use start_at_zero=False for
    quantities without a natural zero. pad_low (in units of one major step)
    leaves room below the lowest point so markers do not sit on the frame.
    """
    lo = 0.0 if start_at_zero else data_min
    span = data_max - lo
    hi_needed = data_max + headroom * span
    lo_needed = lo if start_at_zero else data_min - headroom * span
    step = _nice_step(hi_needed - lo_needed, max_ticks)
    lo_t = math.floor(lo_needed / step + 1e-9) * step
    hi_t = math.ceil(hi_needed / step - 1e-9) * step
    setter = ax.set_ylim if axis == "y" else ax.set_xlim
    which = ax.yaxis if axis == "y" else ax.xaxis
    setter(lo_t - pad_low * step, hi_t)
    which.set_major_locator(mpl.ticker.MultipleLocator(step))
    which.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    decimals = max(0, -math.floor(math.log10(step) + 1e-9))
    if step * 10 ** decimals % 1:          # steps like 2.5 or 0.25
        decimals += 1
    which.set_major_formatter(mpl.ticker.FuncFormatter(
        lambda v, _pos, d=decimals: f"{v:.{d}f}".replace("-", "\u2212")))  # true minus sign
    return lo_t, hi_t, step


# ---------------------------------------------------------------- legend

def _inside(box, xy) -> bool:
    return bool(np.any((xy[:, 0] > box.x0) & (xy[:, 0] < box.x1) &
                       (xy[:, 1] > box.y0) & (xy[:, 1] < box.y1)))


def _legend_hits_data(ax, leg) -> bool:
    ax.figure.canvas.draw()
    box = leg.get_window_extent().expanded(1.05, 1.1)
    for line in ax.get_lines():
        xy = np.column_stack(line.get_data())
        if len(xy):
            if _inside(box, ax.transData.transform(xy.astype(float))):
                return True
    for coll in ax.collections:
        for path in coll.get_paths():
            if len(path.vertices) and _inside(box, ax.transData.transform(path.vertices)):
                return True
    return False


def place_legend(ax, max_raise: int = 3, **kw):
    """Top right first; then top left; then two columns; then raise the axis
    top by one major step and try again. Records the outcome for save()."""
    options = [("upper right", 1), ("upper left", 1), ("upper right", 2), ("upper left", 2)]
    for _ in range(max_raise + 1):
        for loc, ncol in options:
            leg = ax.legend(loc=loc, ncol=ncol, **kw)
            if not _legend_hits_data(ax, leg):
                ax._pubstyle_legend = f"ok ({loc}, {ncol} column)"
                return leg
        ticks = ax.yaxis.get_majorticklocs()
        lo, hi = ax.get_ylim()
        ax.set_ylim(lo, hi + (ticks[1] - ticks[0]))
    leg = ax.legend(loc="upper right", **kw)
    ax._pubstyle_legend = "FAIL: legend covers data, needs a manual decision"
    return leg


# ---------------------------------------------------------------- helpers

def gradient_fill(ax, x, y, color, alpha_top: float = 0.75, zorder: float = 1):
    """XPS-style fill under a curve: strong at the curve, fading to clear at 0.
    Draw the curve itself on top with ax.plot afterwards."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    peak = float(np.nanmax(np.abs(y))) or 1.0
    grad = np.linspace(0, 1, 256)[:, None]
    img = np.ones((256, 1, 4))
    img[..., :3] = to_rgb(color)
    img[..., 3] = alpha_top * grad
    sign = 1 if np.nanmax(y) >= abs(np.nanmin(y)) else -1
    extent = (x.min(), x.max(), 0, peak) if sign > 0 else (x.min(), x.max(), -peak, 0)
    im = ax.imshow(img if sign > 0 else img[::-1], extent=extent, origin="lower",
                   aspect="auto", zorder=zorder, interpolation="bilinear")
    poly = ax.fill_between(x, y, color="none", lw=0)
    im.set_clip_path(poly.get_paths()[0], transform=ax.transData)
    return im


def gap_arrow(ax, x0: float, x1: float, y: float, text_fmt: str = "{:.2f} eV",
              vertical: bool = False):
    """Double arrow with the band gap value. Horizontal for DOS (energy on x),
    vertical for band structures (energy on y)."""
    gap = abs(x1 - x0)
    if vertical:
        ax.annotate("", xy=(y, x1), xytext=(y, x0),
                    arrowprops=dict(arrowstyle="<->", lw=1.2, color="0.15", shrinkA=0, shrinkB=0))
        ax.text(y, (x0 + x1) / 2, " " + text_fmt.format(gap), va="center", ha="left")
    else:
        ax.annotate("", xy=(x1, y), xytext=(x0, y),
                    arrowprops=dict(arrowstyle="<->", lw=1.2, color="0.15", shrinkA=0, shrinkB=0))
        ax.text((x0 + x1) / 2, y, text_fmt.format(gap), va="bottom", ha="center")
    return gap


def incar_value(incar_path: str | Path, tag: str):
    """Value of one INCAR tag as written (string), or None if absent."""
    pat = re.compile(rf"^\s*{re.escape(tag)}\s*=\s*([^#!\n]+)", re.I | re.M)
    m = pat.search(Path(incar_path).read_text(errors="replace"))
    return m.group(1).strip() if m else None


def incar_true(incar_path: str | Path, tag: str) -> bool:
    v = incar_value(incar_path, tag)
    return bool(v) and v.strip(".").upper().startswith("T")


# ---------------------------------------------------------------- checks

# Unicode superscript/subscript characters: forbidden in figure text, write
# them as math instead, e.g. r"cm$^{\rm 2}$" or r"log$_{\rm 10}$".
_UNICODE_SCRIPTS = set("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₒₓ")


def _texts(fig):
    for t in fig.findobj(Text):
        s = t.get_text()
        if s and t.get_visible():
            yield t, s


def check_figure(fig) -> list[str]:
    """Return lines 'PASS ...' / 'FAIL ...' / 'NOTE ...'."""
    out = []
    font = _STATE["font"]
    out.append(f"{'NOTE' if _STATE['standin'] else 'PASS'} font: "
               + (f"{font} used as a DRAFT stand-in for Arial; redraw on a machine with Arial"
                  if _STATE["standin"] else "Arial"))

    bad = []
    for t, s in _texts(fig):
        if _UNICODE_SCRIPTS & set(s):
            bad.append(s)
        plain = re.sub(r"\$[^$]*\$", "", s)
        if "^" in plain or "_" in plain:
            bad.append(s)
    out.append("FAIL text: Unicode or plain-text super/subscripts in " + repr(bad)
               if bad else "PASS text: super/subscripts are rendered as math")

    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    fb = fig.bbox
    cut = []
    for ax in fig.axes:
        bb = ax.get_tightbbox(r)
        for side, over in (("left", fb.x0 - bb.x0), ("bottom", fb.y0 - bb.y0),
                           ("right", bb.x1 - fb.x1), ("top", bb.y1 - fb.y1)):
            if over > 1:
                cut.append(f"{side} edge by {over / fig.dpi * 2.54:.2f} cm")
    out.append("FAIL layout: something is cut off at the canvas " + ", ".join(cut)
               if cut else "PASS layout: nothing cut off at the canvas edges")

    for i, ax in enumerate(fig.axes):
        if hasattr(ax, "_pubstyle_legend"):
            status = ax._pubstyle_legend
            out.append(("PASS" if status.startswith("ok") else "FAIL") + f" legend: {status}")
        elif ax.get_legend() is not None:
            out.append("NOTE legend: placed by hand, check by eye that it covers no data")
        for axis in (ax.xaxis, ax.yaxis):
            off = axis.get_offset_text().get_text()
            if off:
                out.append(f"FAIL axis: corner factor '{off}' shown; put the power of ten "
                           "into the axis title instead, e.g. D (10$^{-9}$ m$^2$ s$^{-1}$)")
        if ax.get_title():
            out.append("FAIL title: journal figures carry no title; move it to the caption")
    return out


def save(fig, name: str, outdir: str | Path = ".") -> list[str]:
    """Save name.png (white, 600 dpi), name_transparent.png, name.pdf, name.svg,
    and name_checks.txt. Prints the checks; returns them."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    checks = check_figure(fig)
    fig.savefig(outdir / f"{name}.png", dpi=600)
    fig.savefig(outdir / f"{name}_transparent.png", dpi=600, transparent=True)
    fig.savefig(outdir / f"{name}.pdf")
    fig.savefig(outdir / f"{name}.svg")
    (outdir / f"{name}_checks.txt").write_text("\n".join(checks) + "\n", encoding="utf-8")
    plt.close(fig)
    print(f"[{name}]")
    for line in checks:
        print("  " + line)
    if any(c.startswith("FAIL") for c in checks):
        print("  -> fix every FAIL before showing this figure to Stormy")
    return checks

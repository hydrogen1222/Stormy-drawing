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
    ps.place_text(ax, "Glass", x_range=(0, 15))  # region name on a free spot
    ps.place_legend(ax)                       # top right unless it covers data or text
    ps.save(fig, "003_Li6PS5Cl_bulk_DOS")     # PNG x2, PDF, SVG, TIFF + checks

Everything here follows the decisions recorded in the skill's SKILL.md.
"""
from __future__ import annotations

import io
import json
import logging
import math
import os
import re
import sys
from pathlib import Path

import numpy as np
import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, to_hex, to_rgb  # noqa: E402
from matplotlib.text import Text  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

# Windows consoles and pipes often use a legacy code page (e.g. GBK); printing
# Å, − or ² must not crash the script there.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="backslashreplace")
    except (AttributeError, ValueError):
        pass

# Version of this style module. A project's figures/_style/pubstyle.py must
# match the skill installed in the project: run
#   python <skill>/scripts/init_figure.py --update-style <project>
# before drawing; it replaces an older copy (the old one goes to _style/archive/).
STYLE_VERSION = "0.5.0"

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
    if sys.platform.startswith("linux"):
        how = ("copy arial.ttf, arialbd.ttf, ariali.ttf, arialbi.ttf to "
               "~/.local/share/fonts/ and delete matplotlib's font cache")
    else:
        how = ("Windows and macOS normally ship Arial; if it was removed, reinstall "
               "it, then delete matplotlib's font cache")
    raise RuntimeError(
        f"Arial is not installed (or not seen by matplotlib). Follow "
        f"references/setup.md: {how}. Do not switch to another font."
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

# Font sizes in pt, at the canvas size (8 cm wide = printed size of a single
# panel). Axis titles slightly larger than tick numbers; legend and labels
# inside the frame the same size as tick numbers, so they never dominate.
LABEL_PT = 7      # axis titles, colorbar title
TICK_PT = 6       # tick numbers
LEGEND_PT = 6     # legend text
ANNOT_PT = 6      # text inside the frame (region names, values, point labels)
DATA_LW = 1.0     # every line 1.0 pt: Nature allows at most 1 pt, Nat. Commun. at least 1 pt
FRAME_LW = 1.0
MAJOR_LEN = 3.2
MINOR_LEN = 1.8
MARKER_SIZE = 4.5

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

REFERENCE_LINE = dict(color="0.45", lw=1.0, ls="--", zorder=0.5, gid="reference")


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
        "font.size": ANNOT_PT, "axes.labelsize": LABEL_PT, "axes.titlesize": LABEL_PT,
        "xtick.labelsize": TICK_PT, "ytick.labelsize": TICK_PT,
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
        "xtick.minor.width": FRAME_LW, "ytick.minor.width": FRAME_LW,
        "xtick.minor.visible": True, "ytick.minor.visible": True,
        "lines.linewidth": DATA_LW, "lines.markersize": MARKER_SIZE,
        "lines.markeredgewidth": DATA_LW,
        "legend.frameon": False, "legend.handlelength": 1.6,
        "legend.handletextpad": 0.5, "legend.labelspacing": 0.3,
        "legend.columnspacing": 1.0, "legend.borderaxespad": 0.5,
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
    cb.set_label(label, fontsize=LABEL_PT)
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


# ---------------------------------------------------------------- overlap

# Everything below works in display (pixel) coordinates. "Hard" obstacles must
# never be covered by a legend or a text label: data lines, markers, filled
# areas, bars, and other text. "Soft" obstacles (reference lines drawn with
# ps.REFERENCE_LINE, axvline/axhline) should be avoided but may be crossed when
# nothing else fits; the check then reports a NOTE.

def _data_based(artist, ax) -> bool:
    try:
        return artist.get_transform().contains_branch(ax.transData)
    except Exception:
        return False


def _densify(v: np.ndarray, step: float = 2.0, closed: bool = False) -> np.ndarray:
    """Points every `step` pixels along a polyline (NaN breaks the line)."""
    if closed and len(v) > 2:
        v = np.vstack([v, v[:1]])
    if len(v) < 2:
        return v[np.isfinite(v).all(axis=1)]
    a, b = v[:-1], v[1:]
    ok = np.isfinite(a).all(axis=1) & np.isfinite(b).all(axis=1)
    a, b = a[ok], b[ok]
    out = [v[np.isfinite(v).all(axis=1)]]
    if len(a):
        n = np.maximum(1, np.ceil(np.hypot(*(b - a).T) / step)).astype(int)
        n = np.minimum(n, 2000)
        idx = np.repeat(np.arange(len(a)), n)
        frac = np.concatenate([np.arange(k) / k for k in n])
        out.append(a[idx] + (b[idx] - a[idx]) * frac[:, None])
    return np.vstack(out)


def _is_visible_style(ls) -> bool:
    return ls not in (None, "None", "none", "", " ")


def _obstacles(ax, skip=()):
    """Return (hard_points, soft_points, polygons, text_boxes).
    *_points: list of (Nx2 array, pad in px). polygons: list of display Paths."""
    fig = ax.figure
    px = fig.dpi / 72.0
    hard, soft, polys, boxes = [], [], [], []
    for line in ax.get_lines():
        if line in skip or not line.get_visible():
            continue
        v = line.get_transform().transform(line.get_path().vertices)
        reference = line.get_gid() == "reference" or not _data_based(line, ax)
        bucket = soft if reference else hard
        if _is_visible_style(line.get_linestyle()) and line.get_linewidth() > 0:
            bucket.append((_densify(v), line.get_linewidth() * px / 2))
        marker = line.get_marker()
        if _is_visible_style(marker):
            half, edge = line.get_markersize() / 2 * px, line.get_markeredgewidth() / 2 * px
            pad = {"_": (half + edge, edge), "|": (edge, half + edge)}.get(
                marker, half + edge)                 # flat markers: error bar caps
            bucket.append((v[np.isfinite(v).all(axis=1)], pad))
    for coll in ax.collections:
        if coll in skip or not coll.get_visible():
            continue
        name = type(coll).__name__
        if name in ("QuadMesh",):
            continue
        if name == "PathCollection":            # scatter
            off = coll.get_offset_transform().transform(coll.get_offsets())
            sizes = coll.get_sizes()
            pad = (np.sqrt(sizes.max()) / 2 if len(sizes) else 3) * px
            hard.append((off[np.isfinite(off).all(axis=1)], pad))
            continue
        if not _data_based(coll, ax):
            continue
        tr = coll.get_transform()
        for path in coll.get_paths():
            if not len(path.vertices):
                continue
            dpath = tr.transform_path(path)
            if name == "LineCollection":
                hard.append((_densify(dpath.vertices), max(coll.get_linewidths()) * px / 2))
            else:
                hard.append((_densify(dpath.vertices, closed=True), 0.0))
                polys.append(dpath)
    for patch in ax.patches:
        if patch in skip or not patch.get_visible() or not _data_based(patch, ax):
            continue                            # axvspan backgrounds are not data
        dpath = patch.get_transform().transform_path(patch.get_path())
        hard.append((_densify(dpath.vertices, closed=True), 0.0))
        polys.append(dpath)
    r = fig.canvas.get_renderer()
    for t in ax.texts:
        if t in skip or not t.get_visible() or not t.get_text().strip():
            continue
        boxes.append((t, t.get_window_extent(r)))
    leg = ax.get_legend()
    if leg is not None and leg not in skip:
        boxes.append((leg, leg.get_window_extent(r)))
    return hard, soft, polys, boxes


def _box_hits(box, groups) -> int:
    hits = 0
    for pts, pad in groups:
        padx, pady = pad if isinstance(pad, tuple) else (pad, pad)
        if len(pts) and np.any((pts[:, 0] > box.x0 - padx) & (pts[:, 0] < box.x1 + padx) &
                               (pts[:, 1] > box.y0 - pady) & (pts[:, 1] < box.y1 + pady)):
            hits += 1
    return hits


def _box_in_polys(box, polys) -> bool:
    probe = np.array([[box.x0, box.y0], [box.x1, box.y0], [box.x0, box.y1],
                      [box.x1, box.y1], [(box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2]])
    return any(p.contains_points(probe).any() for p in polys)


def _overlaps(a, b) -> bool:
    return a.x0 < b.x1 and b.x0 < a.x1 and a.y0 < b.y1 and b.y0 < a.y1


def _assess(ax, artist, box, margin_pt: float = 1.5, obs=None):
    """(hard_problems, soft_problems) for a legend or text box. obs: obstacles
    from _obstacles(ax, skip=(artist,)), passed in when testing many spots."""
    px = ax.figure.dpi / 72.0
    box = box.expanded(1, 1).padded(margin_pt * px)
    hard, soft, polys, boxes = obs or _obstacles(ax, skip=(artist,))
    problems = []
    if _box_hits(box, hard) or _box_in_polys(box, polys):
        problems.append("covers data")
    others = [o for o, b in boxes if _overlaps(box, b)]
    if others:
        problems.append("touches other text or the legend")
    ab = ax.get_window_extent()
    inner = box.padded(-margin_pt * px)
    if inner.x0 < ab.x0 or inner.x1 > ab.x1 or inner.y0 < ab.y0 or inner.y1 > ab.y1:
        problems.append("crosses the frame")
    soft_hits = ["crosses a reference line"] if _box_hits(box, soft) else []
    return problems, soft_hits


# ---------------------------------------------------------------- legend

LEGEND_LOCS = ("upper right", "upper left", "lower left", "lower right",
               "center right", "center left", "upper center", "lower center")


def place_legend(ax, ncols=(1, 2), max_raise: int = 1, locs=LEGEND_LOCS, **kw):
    """Put the legend where it covers no data, no text and stays inside the frame.

    Tries top right first, then the other corners and edges, in one and then two
    columns. If nothing fits, raises the axis top by one major step (max_raise
    times) and tries again. A spot that only crosses a reference line is used
    as a last resort (reported as NOTE). Records the outcome for save()."""
    fig = ax.figure
    fig.canvas.draw()
    lo, hi = ax.get_ylim()
    ax._pubstyle_legend_job = dict(ncols=ncols, max_raise=max_raise, locs=locs, **kw)
    fallback = None
    if ax.get_legend() is not None:
        ax.get_legend().remove()
    ticks = ax.yaxis.get_majorticklocs()
    step = ticks[1] - ticks[0] if len(ticks) > 1 else (hi - lo) / 5
    if ax.get_yscale() != "linear":
        max_raise = 0                           # one linear step means nothing on a log axis
    for k in range(max_raise + 1):
        if k:
            ax.set_ylim(lo, hi + k * step)
        obs = _obstacles(ax)
        for ncol in ncols:
            for loc in locs:
                leg = ax.legend(loc=loc, ncol=ncol, **kw)
                box = leg.get_window_extent(fig.canvas.get_renderer())
                hard, soft = _assess(ax, leg, box, obs=obs)
                if not hard and not soft:
                    note = f" after raising the axis top by {k} step" if k else ""
                    ax._pubstyle_legend = f"ok ({loc}, {ncol} column{note})"
                    ax._pubstyle_raised = ((lo, hi), ax.get_ylim()) if k else None
                    return leg
                if not hard and fallback is None and k == 0:
                    fallback = (loc, ncol)
    ax.set_ylim(lo, hi)
    ax._pubstyle_raised = None
    if fallback:
        leg = ax.legend(loc=fallback[0], ncol=fallback[1], **kw)
        ax._pubstyle_legend = f"note ({fallback[0]}, {fallback[1]} column): crosses a reference line"
        return leg
    leg = ax.legend(loc="upper right", **kw)
    ax._pubstyle_legend = ("FAIL: no free spot for the legend. Shorten the labels, use "
                           "ps.factor_legend, or label curves directly with ps.label_point")
    return leg


def factor_legend(colors: dict, styles: dict, neutral: str = "0.25"):
    """Handles for a legend that explains two factors separately, instead of one
    entry per combination. Example: color = interface, line style = method:

        h, l = ps.factor_legend({"Interface 1": c1, "Interface 2": c2},
                                {"MACE": dict(marker="o", ls="-"),
                                 "GRACE": dict(marker="s", ls="--")})
        ps.place_legend(ax, handles=h, labels=l, ncols=(2, 1))

    Four entries become 2 + 2, half as long, and the reader decodes them faster."""
    from matplotlib.lines import Line2D
    handles, labels = [], []
    for lab, c in colors.items():
        handles.append(Line2D([], [], color=c, lw=DATA_LW))
        labels.append(lab)
    for lab, st in styles.items():
        st = {"color": neutral, "mfc": "white", "lw": DATA_LW, **st}
        handles.append(Line2D([], [], **st))
        labels.append(lab)
    return handles, labels


# ---------------------------------------------------------------- text labels

def _try_text(ax, text, xy_axes, obs=None):
    text.set_position(xy_axes)
    box = text.get_window_extent(ax.figure.canvas.get_renderer())
    return _assess(ax, text, box, obs=obs)


def place_text(ax, s: str, x_range=None, y_range=None, prefer: str = "bottom", **kw):
    """Put a label (e.g. a region name "Crystal") at a free spot.

    x_range / y_range are data limits of the region the label belongs to (default:
    the whole axis). prefer = "bottom" or "top": where in that region to look
    first. The label avoids data, other text and the legend. If no spot is free,
    it is put at the preferred spot and the check reports FAIL."""
    fig = ax.figure
    fig.canvas.draw()
    to_ax = ax.transAxes.inverted()
    def ax_span(rng, axis):
        if rng is None:
            return 0.0, 1.0
        pts = np.array([[rng[0], 0], [rng[1], 0]]) if axis == "x" else np.array([[0, rng[0]], [0, rng[1]]])
        a = to_ax.transform(ax.transData.transform(pts))[:, 0 if axis == "x" else 1]
        return float(np.clip(a.min(), 0, 1)), float(np.clip(a.max(), 0, 1))
    x0, x1 = ax_span(x_range, "x")
    y0, y1 = ax_span(y_range, "y")
    t = ax.text(0, 0, s, transform=ax.transAxes, ha="center", va="center",
                fontsize=ANNOT_PT, **kw)
    t._pubstyle_job = (place_text, (ax, s), dict(x_range=x_range, y_range=y_range,
                                                 prefer=prefer, **kw))
    xs = np.linspace(x0, x1, 23)[1:-1]
    xs = xs[np.argsort(abs(xs - (x0 + x1) / 2))]           # middle first
    ys = np.linspace(y0, y1, 23)[1:-1]
    ys = ys if prefer == "bottom" else ys[::-1]
    best = None
    obs = _obstacles(ax, skip=(t,))
    for y in ys:
        for x in xs:
            hard, soft = _try_text(ax, t, (x, y), obs)
            if not hard and not soft:
                t._pubstyle_placed = "ok"
                return t
            if not hard and best is None:
                best = (x, y)
    if best:
        t.set_position(best)
        t._pubstyle_placed = "note: crosses a reference line"
    else:
        t.set_position(((x0 + x1) / 2, ys[0]))
        t._pubstyle_placed = "FAIL: no free spot"
    return t


def _two_lines(s: str) -> str | None:
    """Split a long label into two lines at " (" or else at the middle space,
    outside math. 'beta-Li3PS4 (bulk)' -> 'beta-Li3PS4' / '(bulk)'."""
    if "\n" in s:
        return None
    plain = [i for i, ch in enumerate(s) if ch == " " and s[:i].count("$") % 2 == 0]
    if not plain:
        return None
    paren = [i for i in plain if s[i + 1:i + 2] == "("]
    i = paren[-1] if paren else min(plain, key=lambda k: abs(k - len(s) / 2))
    return s[:i] + "\n" + s[i + 1:]


def label_point(ax, x: float, y: float, s: str, gap_pt: float = 3.0, **kw):
    """Label one data point (e.g. an experimental value) right next to it:
    tries right, left, above, below and the diagonals, takes the first free spot.
    If a one-line label fits nowhere, tries again with it split into two lines
    (at " (" when there is one). The label is tied to the point, so it moves with
    it if the axis limits change."""
    fig = ax.figure
    fig.canvas.draw()
    d = gap_pt + MARKER_SIZE / 2 + DATA_LW / 2
    t = ax.annotate(s, xy=(x, y), xytext=(0, 0), textcoords="offset points",
                    fontsize=ANNOT_PT, **kw)
    t._pubstyle_job = (label_point, (ax, x, y, s), dict(gap_pt=gap_pt, **kw))
    r = fig.canvas.get_renderer()
    options = [((d, 0), "left", "center"), ((-d, 0), "right", "center"),
               ((0, d), "center", "bottom"), ((0, -d), "center", "top"),
               ((d, d), "left", "bottom"), ((-d, d), "right", "bottom"),
               ((d, -d), "left", "top"), ((-d, -d), "right", "top")]
    best = None
    obs = _obstacles(ax, skip=(t,))
    texts = [s] + ([_two_lines(s)] if _two_lines(s) else [])
    for text in texts:
        t.set_text(text)
        for off, ha, va in options:
            t.set_ha(ha)
            t.set_va(va)
            t.set_multialignment(ha)
            t.xyann = off
            t.update_positions(r)
            hard, soft = _assess(ax, t, t.get_window_extent(r), obs=obs)
            if not hard and not soft:
                t._pubstyle_placed = "ok"
                return t
            if not hard and best is None:
                best = (text, off, ha, va)
    text, off, ha, va = best or (s, *options[0])
    t.set_text(text)
    t.set_ha(ha)
    t.set_va(va)
    t.set_multialignment(ha)
    t.xyann = off
    t._pubstyle_placed = "note: crosses a reference line" if best else "FAIL: no free spot"
    return t


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
                    arrowprops=dict(arrowstyle="<->", lw=DATA_LW, color="0.15", shrinkA=0, shrinkB=0))
        ax.text(y, (x0 + x1) / 2, " " + text_fmt.format(gap), va="center", ha="left")
    else:
        ax.annotate("", xy=(x1, y), xytext=(x0, y),
                    arrowprops=dict(arrowstyle="<->", lw=DATA_LW, color="0.15", shrinkA=0, shrinkB=0))
        ax.text((x0 + x1) / 2, y, text_fmt.format(gap), va="bottom", ha="center")
    return gap


def incar_value(incar_path: str | Path, tag: str):
    """Value of one INCAR tag as written (string), or None if absent."""
    pat = re.compile(rf"^\s*{re.escape(tag)}\s*=\s*([^#!\n]+)", re.I | re.M)
    m = pat.search(Path(incar_path).read_text(encoding="utf-8", errors="replace"))
    return m.group(1).strip() if m else None


def incar_true(incar_path: str | Path, tag: str) -> bool:
    v = incar_value(incar_path, tag)
    return bool(v) and v.strip(".").upper().startswith("T")


def smooth_density(H, sigma_bins: float, periodic: bool = True):
    """Gaussian smoothing of a 2D histogram (e.g. Li probability density).

    sigma_bins is the Gaussian width in bins (sigma in Å / bin width in Å).
    periodic=True wraps around the cell edges (MD in a periodic cell). The
    kernel is normalized, so the total (number of atoms) is unchanged.
    Write the bin width and sigma into the figure README."""
    H = np.asarray(H, float)
    if sigma_bins <= 0:
        return H.copy()
    half = int(math.ceil(4 * sigma_bins))
    k = np.exp(-0.5 * (np.arange(-half, half + 1) / sigma_bins) ** 2)
    k /= k.sum()
    mode = "wrap" if periodic else "reflect"
    out = H
    for axis in (0, 1):
        pad = [(0, 0), (0, 0)]
        pad[axis] = (half, half)
        padded = np.pad(out, pad, mode=mode)
        out = np.apply_along_axis(lambda v: np.convolve(v, k, mode="valid"), axis, padded)
    return out


# ---------------------------------------------------------------- checks

# Unicode superscript/subscript characters: forbidden in figure text, write
# them as math instead, e.g. r"cm$^{\rm 2}$" or r"log$_{\rm 10}$".
_UNICODE_SCRIPTS = set("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₒₓ")


def _texts(fig):
    for t in fig.findobj(Text):
        s = t.get_text()
        if s and t.get_visible():
            yield t, s


def _check_overlaps(fig, r) -> list[str]:
    """Every legend and every text label inside the frame: does it cover data,
    touch another text, cross the frame or a reference line?"""
    out, notes = [], []
    for ax in fig.axes:
        items = [t for t in ax.texts if t.get_visible() and t.get_text().strip()]
        leg = ax.get_legend()
        if leg is not None:
            items.append(leg)
        for it in items:
            name = "legend" if it is leg else f"text '{it.get_text()}'"
            hard, soft = _assess(ax, it, it.get_window_extent(r))
            if hard:
                out.append(f"FAIL overlap: {name} " + ", ".join(hard))
            elif soft:
                notes.append(f"NOTE overlap: {name} {soft[0]}; acceptable only if no "
                             "better place exists")
        if leg is not None and not hasattr(ax, "_pubstyle_legend_job"):
            out.append("FAIL legend: not placed by ps.place_legend (ax.legend by hand is "
                       "not allowed); call ps.place_legend(ax, ...) instead")
        if leg is not None and getattr(ax, "_pubstyle_legend", "").startswith("ok") \
                and "raising" in ax._pubstyle_legend:
            notes.append(f"NOTE legend: {ax._pubstyle_legend}; if the data now look "
                         "squashed, try ps.factor_legend or shorter labels")
    if not out:
        out.append("PASS overlap: legend and labels cover no data, no other text, "
                   "and stay inside the frame")
    return out + notes


def check_figure(fig) -> list[str]:
    """Return lines 'PASS ...' / 'FAIL ...' / 'NOTE ...'."""
    out = []
    font = _STATE["font"]
    out.append(f"NOTE style: pubstyle {STYLE_VERSION}")
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

    out.extend(_check_overlaps(fig, r))
    for i, ax in enumerate(fig.axes):
        for axis in (ax.xaxis, ax.yaxis):
            off = axis.get_offset_text().get_text()
            if off:
                out.append(f"FAIL axis: corner factor '{off}' shown; put the power of ten "
                           "into the axis title instead, e.g. D (10$^{-9}$ m$^2$ s$^{-1}$)")
        if ax.get_title():
            out.append("FAIL title: journal figures carry no title; move it to the caption")
    return out


def refresh_placements(fig) -> None:
    """Redo every place_text / label_point / place_legend of this figure with the
    final axis limits (save() calls this). So the order of calls in plot.py does
    not matter: labels first, legend last, each avoiding the others."""
    for ax in fig.axes:
        jobs = [t._pubstyle_job for t in list(ax.texts) if hasattr(t, "_pubstyle_job")]
        legend_job = getattr(ax, "_pubstyle_legend_job", None)
        if not jobs and not legend_job:
            continue
        for t in [t for t in ax.texts if hasattr(t, "_pubstyle_job")]:
            t.remove()
        leg = ax.get_legend()
        if legend_job and leg is not None:
            leg.remove()
            raised = getattr(ax, "_pubstyle_raised", None)
            if raised and np.allclose(ax.get_ylim(), raised[1]):
                ax.set_ylim(*raised[0])          # undo our own raise, keep user limits
        for fn, args, kw in jobs:
            fn(*args, **kw)
        if legend_job:
            place_legend(ax, **legend_job)


TIFF_DPI = 1200   # journals ask 1000-1200 dpi for raster line art (CCL/Elsevier 1000, ACS 1200)


def _save_tiff(fig, path: Path) -> None:
    """White-background RGB TIFF with lossless LZW compression, for journals
    that want TIFF instead of (or as well as) the vector PDF."""
    from PIL import Image
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=TIFF_DPI, facecolor="white")
    buf.seek(0)
    with Image.open(buf) as im:
        im.convert("RGB").save(path, format="TIFF", compression="tiff_lzw",
                               dpi=(TIFF_DPI, TIFF_DPI))


def save(fig, name: str, outdir: str | Path = ".") -> list[str]:
    """Save name.png (white, 600 dpi), name_transparent.png, name.pdf, name.svg,
    name.tif (white, 1200 dpi, RGB, LZW) and name_checks.txt.
    Prints the checks; returns them."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    refresh_placements(fig)
    checks = check_figure(fig)
    fig.savefig(outdir / f"{name}.png", dpi=600)
    fig.savefig(outdir / f"{name}_transparent.png", dpi=600, transparent=True)
    fig.savefig(outdir / f"{name}.pdf")
    fig.savefig(outdir / f"{name}.svg")
    _save_tiff(fig, outdir / f"{name}.tif")
    (outdir / f"{name}_checks.txt").write_text("\n".join(checks) + "\n", encoding="utf-8")
    plt.close(fig)
    print(f"[{name}]")
    for line in checks:
        print("  " + line)
    if any(c.startswith("FAIL") for c in checks):
        print("  -> fix every FAIL before showing this figure to Stormy")
    return checks

"""Vector parts for assembling figures in an image editor (Photoshop, Illustrator,
Affinity, Inkscape) -- the things a VMD / VESTA / OVITO picture needs around it.

Every part is a small figure in the project's style (Arial bold, 1 pt lines, the
colour mode of pubstyle) with a transparent background; save it with
ps.save_modes like any other figure and drag the PDF or SVG into the layout.
Sizes are given in cm and are real: a part saved as 3.0 cm stays 3.0 cm.

    import pubstyle as ps
    import pubparts as pp

    def draw():
        return pp.colorbar(-0.05, 0.05, r"ESP (a.u.)")          # Turbo, like VMD

    ps.save_modes(draw, HERE.name, HERE)

Parts (each returns a figure; the drawing helpers at the bottom put arrows,
dashed boxes and distance lines onto a part from new_part):

  colorbar            colour bar of a colour scale (default "turbo" = VMD's Turbo)
  isosurface_legend   coloured swatches with the isovalues, e.g. +0.002 / -0.002
  element_legend      atom colour dots with element symbols
  axes_triad          x/y/z (or a/b/c) arrows for a given view; VMD rotate_matrix works
  scale_bar           length bar with a label, e.g. 5 Angstrom
  region_strip        Crystal | Glass style strips with dashed boundaries
  level_diagram       energy levels per column (HOMO/LUMO, band edges), with links
  add_inset           zoom inset with connector lines for any ordinary figure
  new_part, label, arrow, dashed_box, dashed_circle, dimension, line   free layout
"""
from __future__ import annotations

import math

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import Colormap, ListedColormap, Normalize
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle

import pubstyle as ps

CM = ps.CM
INK = "0.15"                      # the dark grey of every line and label in the parts
DASH = (0, (4, 3))                # dashed lines, in units of the line width
# Sign colours of isosurfaces and charge-difference maps: the ends of ps.DIVERGING
# (negative blue, positive red), so a legend matches a map drawn with it.
SIGN_COLORS = {"+": "#A8322A", "-": "#2D4F8F"}


# ---------------------------------------------------------------- canvas and drawing helpers

def new_part(width_cm: float, height_cm: float):
    """Empty transparent canvas of exactly width x height cm. Returns (fig, ax); ax
    uses cm as its units, origin bottom left, nothing is drawn but what you add."""
    if not (0.3 <= width_cm <= 30 and 0.3 <= height_cm <= 30):
        raise ValueError(f"part size {width_cm} x {height_cm} cm is outside 0.3 to 30 cm; "
                         "check that you passed cm, not pixels or Angstrom")
    if ps._STATE["font"] is None:
        ps.apply()
    fig = plt.figure(figsize=(width_cm * CM, height_cm * CM))
    fig.patch.set_alpha(0)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, width_cm)
    ax.set_ylim(0, height_cm)
    ax.axis("off")
    ax._pubstyle_part = True          # lets check_figure treat it as a free layout
    fig._pubstyle_canvas = "part"
    return fig, ax


def label(ax, x: float, y: float, text: str, ha: str = "left", va: str = "center",
          size: float = ps.ANNOT_PT, italic: bool = False, rotation: float = 0.0, color=INK):
    """Bold label at (x, y) cm."""
    return ax.text(x, y, text, ha=ha, va=va, fontsize=size, fontweight="bold",
                   fontstyle="italic" if italic else "normal", rotation=rotation,
                   color=color, clip_on=False)


def line(ax, p0, p1, dashed: bool = False, color=INK):
    return ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=color, lw=ps.DATA_LW,
                   ls=DASH if dashed else "-", solid_capstyle="butt", clip_on=False)[0]


def arrow(ax, p0, p1, color=INK, both: bool = False):
    """Arrow from p0 to p1 (cm), 1 pt shaft, small closed head."""
    style = "<|-|>" if both else "-|>"
    return ax.annotate("", xy=p1, xytext=p0, annotation_clip=False,
                       arrowprops=dict(arrowstyle=style, lw=ps.DATA_LW, color=color,
                                       shrinkA=0, shrinkB=0, mutation_scale=6))


def dashed_box(ax, x: float, y: float, w: float, h: float, color=INK):
    """Dashed rectangle with lower-left corner (x, y), for marking a region of a picture."""
    r = Rectangle((x, y), w, h, fill=False, ec=color, lw=ps.DATA_LW, ls=DASH, clip_on=False)
    ax.add_patch(r)
    return r


def dashed_circle(ax, cx: float, cy: float, radius: float, color=INK):
    c = Circle((cx, cy), radius, fill=False, ec=color, lw=ps.DATA_LW, ls=DASH, clip_on=False)
    ax.add_patch(c)
    return c


def dimension(ax, p0, p1, text: str, offset: float = 0.0, cap: float = 0.10, gap: float = 0.12,
              color=INK):
    """Distance annotation: a line from p0 to p1 with end caps and the text beside its
    middle. offset moves the whole dimension line sideways (cm, left of p0->p1 is +)."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    d = p1 - p0
    n = np.hypot(*d)
    if n == 0:
        raise ValueError("dimension: the two end points are the same")
    u = d / n
    nrm = np.array([-u[1], u[0]])
    a, b = p0 + nrm * offset, p1 + nrm * offset
    line(ax, a, b, color=color)
    for p in (a, b):
        line(ax, p - nrm * cap / 2, p + nrm * cap / 2, color=color)
    mid = (a + b) / 2 + nrm * gap
    ang = math.degrees(math.atan2(u[1], u[0]))
    ang = ang - 180 if ang > 90 else ang + 180 if ang < -90 else ang
    return label(ax, *mid, text, ha="center", va="bottom", rotation=ang, color=color)


def _text_cm(text: str, size: float = ps.ANNOT_PT) -> float:
    """Width of a bold label in cm, measured with the real font."""
    if ps._STATE["font"] is None:
        ps.apply()
    fig = plt.figure(figsize=(1, 1))
    t = fig.text(0, 0, text, fontsize=size, fontweight="bold")
    w = t.get_window_extent(fig.canvas.get_renderer()).width / fig.dpi * 2.54
    plt.close(fig)
    return w


def _nice_ticks(vmin, vmax, n=5):
    loc = mpl.ticker.MaxNLocator(n, steps=[1, 2, 2.5, 5, 10])
    return [t for t in loc.tick_values(vmin, vmax) if vmin - 1e-12 <= t <= vmax + 1e-12]


# ---------------------------------------------------------------- 1. colour bar

def colorbar(vmin: float, vmax: float, title: str, cmap="turbo", orientation: str = "vertical",
             length_cm: float = 6.0, thickness_cm: float = 0.22, ticks=None,
             decimals: int | None = None, bands: int | None = None, reverse: bool = False,
             extend: str = "neither"):
    """Colour bar for a colour scale. The default "turbo" is the scale VMD 1.9.4 calls
    Turbo (Google's table, 256 entries). Give the same vmin / vmax as the Color Scale
    Data Range in VMD: the first value is the first colour, the last value the last
    colour, in between linear. It never follows the soft colour mode: a colour bar must
    stay identical to the picture it belongs to.

    Things to adjust (cm; all the text stays at the style's fixed sizes):
      length_cm, thickness_cm   size of the bar itself (long and thin: 6 x 0.22 by default)
      ticks      None = about 5 round values; an int n = n equal steps from vmin to vmax
                 (VMD's own bar uses 11); or an explicit list of values
      decimals   digits after the decimal point on the tick labels (0 = integers);
                 None = as short as the values allow
      bands      n flat colour bands (VMD's posterize); reverse=True swaps the ends
      extend     "min" / "max" / "both" adds an arrow-like end for out-of-range values
    The canvas is cut to the content (0.12 cm margin), so the part's size is the size of
    what is drawn. Tick labels that would touch each other are an error, not a surprise:
    use fewer ticks, fewer decimals or a longer bar."""
    if not (math.isfinite(vmin) and math.isfinite(vmax) and vmin < vmax):
        raise ValueError(f"vmin {vmin} must be smaller than vmax {vmax}")
    if orientation not in ("vertical", "horizontal"):
        raise ValueError("orientation must be 'vertical' or 'horizontal'")
    if extend not in ("neither", "min", "max", "both"):
        raise ValueError("extend must be neither, min, max or both")
    if not (1.0 <= length_cm <= 20.0):
        raise ValueError("length_cm must be between 1 and 20 cm")
    if not (0.05 <= thickness_cm <= 2.0):
        raise ValueError("thickness_cm must be between 0.05 and 2 cm")
    if decimals is not None and not (0 <= int(decimals) <= 6):
        raise ValueError("decimals must be between 0 and 6")
    base = plt.get_cmap(cmap) if not isinstance(cmap, Colormap) else cmap
    if bands is not None:
        if bands < 2 or bands > 64:
            raise ValueError("bands must be between 2 and 64")
        base = ListedColormap(base(np.linspace(0, 1, bands)))
    if reverse:
        base = base.reversed()
    if ticks is None:
        tick_values = _nice_ticks(vmin, vmax)
    elif isinstance(ticks, (int, np.integer)) and not isinstance(ticks, bool):
        if not (2 <= ticks <= 30):
            raise ValueError("ticks as a number must be between 2 and 30")
        tick_values = list(np.linspace(vmin, vmax, int(ticks)))
    else:
        tick_values = [float(t) for t in ticks]
        if any(not (vmin - 1e-9 <= t <= vmax + 1e-9) for t in tick_values):
            raise ValueError("every tick must lie between vmin and vmax")
    formatter = None
    if decimals is not None:
        formatter = mpl.ticker.FuncFormatter(
            lambda v, _pos, d=int(decimals): f"{v:.{d}f}".replace("-", "\u2212"))

    def build(canvas_w, canvas_h, x0, y0):
        """x0, y0: lower-left corner of the bar on the canvas (cm)."""
        fig, _ = new_part(canvas_w, canvas_h)
        fig.delaxes(fig.axes[0])
        bw, bh = (thickness_cm, length_cm) if orientation == "vertical" else (length_cm, thickness_cm)
        cax = fig.add_axes((x0 / canvas_w, y0 / canvas_h, bw / canvas_w, bh / canvas_h))
        cax._pubstyle_colorbar = True
        cb = fig.colorbar(mpl.cm.ScalarMappable(Normalize(vmin, vmax), base), cax=cax,
                          orientation=orientation, extend=extend, ticks=tick_values,
                          format=formatter)
        cb.set_label(title, fontsize=ps.LABEL_PT)
        cb.outline.set_linewidth(ps.FRAME_LW)
        cb.ax.tick_params(direction="out", width=ps.FRAME_LW, length=ps.MAJOR_LEN)
        cb.ax.minorticks_off()
        fig._pubstyle_part_name = "colorbar"
        return fig, cax

    # pass 1 on a roomy canvas to measure the real extent, pass 2 cuts the canvas to it
    big = 30.0
    fig, cax = build(big, big, 10.0, 10.0)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    labels = [t for t in (cax.get_yticklabels() if orientation == "vertical" else cax.get_xticklabels())
              if t.get_text() and t.get_visible()]
    boxes = sorted((t.get_window_extent(r) for t in labels),
                   key=lambda b: b.y0 if orientation == "vertical" else b.x0)
    gap_px = 0.08 / 2.54 * fig.dpi                           # 0.08 cm of air between neighbours
    for b0, b1 in zip(boxes, boxes[1:]):
        touching = (b0.y1 + gap_px > b1.y0) if orientation == "vertical" else (b0.x1 + gap_px > b1.x0)
        if touching:
            plt.close(fig)
            raise ValueError("colorbar tick labels touch each other; use fewer ticks "
                             "(ticks=5), fewer decimals (decimals=0) or a longer bar (length_cm)")
    tb = fig.get_tightbbox(r)                                # inches
    x_lo, x_hi, y_lo, y_hi = (v * 2.54 for v in (tb.x0, tb.x1, tb.y0, tb.y1))
    plt.close(fig)
    margin = 0.12
    w = x_hi - x_lo + 2 * margin
    h = y_hi - y_lo + 2 * margin
    fig, _ = build(w, h, 10.0 - x_lo + margin, 10.0 - y_lo + margin)
    return fig


# ---------------------------------------------------------------- 2. isosurface legend

def _fmt_level(v: float) -> str:
    s = f"{abs(v):g}"
    return ("+" if v > 0 else "−" if v < 0 else "") + s


def isosurface_legend(levels, unit: str = "", title: str | None = None,
                      orientation: str = "horizontal"):
    """Swatches with isovalues. levels = [(0.002, "#A8322A"), (-0.002, "#2D4F8F")] or just
    [0.002, -0.002] (then the sign colours SIGN_COLORS are used). unit e.g.
    r"e $\\rm\\AA^{-3}$"; title e.g. "Isovalue". Colours follow the colour mode."""
    items = []
    for lv in levels:
        v, c = (lv if isinstance(lv, (tuple, list)) else (lv, None))
        if not math.isfinite(v):
            raise ValueError(f"isovalue {v!r} is not a finite number")
        items.append((v, c or SIGN_COLORS["+" if v > 0 else "-"]))
    if not items:
        raise ValueError("levels is empty")
    txt = [(_fmt_level(v) + (f" {unit}" if unit else "")) for v, _ in items]
    sw, pad, row = 0.32, 0.12, 0.5
    width_txt = max(_text_cm(s) for s in txt) + 0.05
    if orientation == "horizontal":
        w = 0.1 + len(items) * (sw + pad + width_txt + 0.25) - 0.15
        h = row + (0.45 if title else 0.1)
    else:
        w = 0.1 + sw + pad + width_txt + 0.1
        h = len(items) * row + (0.45 if title else 0.1)
    fig, ax = new_part(w, h)
    y_top = h - (0.45 if title else 0.05)
    if title:
        label(ax, 0.1, h - 0.2, title)
    for i, ((v, c), s) in enumerate(zip(items, txt)):
        if orientation == "horizontal":
            x, y = 0.1 + i * (sw + pad + width_txt + 0.2), y_top - row / 2
        else:
            x, y = 0.1, y_top - row / 2 - i * row
        ax.add_patch(FancyBboxPatch((x, y - sw / 2), sw, sw, boxstyle="round,pad=0,rounding_size=0.06",
                                    fc=ps.tone(c), ec=INK, lw=ps.DATA_LW, clip_on=False))
        label(ax, x + sw + pad, y, s)
    return fig


# ---------------------------------------------------------------- 3. element legend

def element_legend(elements, reg=None, colors: dict | None = None, orientation: str = "horizontal",
                   ncols: int | None = None):
    """Coloured dots with element symbols. Colours come from the project's colour
    registry (the same as in the curves) unless given in `colors`, e.g. to match the
    atom colours of the picture: colors={"Li": "#7B3FA0"} (exact hex, not softened)."""
    names = [ps.element_symbol(e) for e in elements]
    if not names:
        raise ValueError("elements is empty")
    if len(set(names)) != len(names):
        raise ValueError(f"elements has duplicates: {names}")
    if colors is None:
        reg = reg or ps.ColorRegistry()
    cols = [(colors or {}).get(n) or reg.color(n) for n in names]
    if orientation not in ("horizontal", "vertical"):
        raise ValueError("orientation must be 'horizontal' or 'vertical'")
    ncols = ncols or (len(names) if orientation == "horizontal" else 1)
    nrows = math.ceil(len(names) / ncols)
    r, dy = 0.15, 0.5
    dx = 2 * r + 0.12 + max(_text_cm(n) for n in names) + 0.3
    fig, ax = new_part(0.15 + ncols * dx - 0.2, nrows * dy + 0.1)
    for i, (n, c) in enumerate(zip(names, cols)):
        row, col = divmod(i, ncols)
        x, y = 0.15 + r + col * dx, nrows * dy + 0.05 - dy / 2 - row * dy
        ax.add_patch(Circle((x, y), r, fc=c, ec=INK, lw=ps.DATA_LW, clip_on=False))
        label(ax, x + r + 0.12, y, n)
    return fig


# ---------------------------------------------------------------- 4. axes triad and scale bar

def _rotation3(rotation):
    if rotation is None:
        return np.eye(3)
    m = np.asarray(rotation, float)
    if m.shape == (4, 4):
        m = m[:3, :3]
    if m.shape != (3, 3):
        raise ValueError("rotation must be 3x3 or the 4x4 matrix from VMD "
                         "(molinfo top get rotate_matrix)")
    if not np.allclose(m @ m.T, np.eye(3), atol=1e-3):
        raise ValueError("rotation is not a pure rotation (rows must be orthonormal)")
    return m


def axes_triad(rotation=None, labels=("x", "y", "z"), length_cm: float = 1.0,
               vectors=None):
    """Three arrows for the viewing direction. rotation: 3x3 or VMD's 4x4 rotate_matrix
    (screen = R @ v, x right, y up, z toward the viewer); default is the straight view.
    vectors: the three axes as Cartesian vectors (rows), e.g. the lattice vectors for
    a, b, c of a non-orthogonal cell; default x, y, z. Axes pointing at the viewer are
    drawn short, as they are in the picture."""
    R = _rotation3(rotation)
    V = np.eye(3) if vectors is None else np.asarray(vectors, float)
    if V.shape != (3, 3) or abs(np.linalg.det(V)) < 1e-9:
        raise ValueError("vectors must be three independent 3-vectors (one per row)")
    V = V / np.linalg.norm(V, axis=1)[:, None]
    if len(labels) != 3:
        raise ValueError("labels needs three entries")
    screen = (R @ V.T).T                       # (3, 3): x, y, depth per axis
    pad = 0.45
    size = 2 * (length_cm + pad)
    fig, ax = new_part(size, size)
    c = np.array([size / 2, size / 2])
    for i in np.argsort(screen[:, 2]):         # far first, near last
        d = screen[i, :2] * length_cm
        n = np.hypot(*d)
        tip = c + d
        if n < 0.12:                           # (almost) along the view axis: a dot
            ax.add_patch(Circle(c, 0.05, fc=INK, ec=INK, lw=ps.DATA_LW, clip_on=False))
            dirn = np.array([0.7, 0.7])
        else:
            arrow(ax, c, tip)
            dirn = d / n
        label(ax, *(tip + dirn * 0.22), labels[i], ha="center", va="center", italic=True)
    return fig


def scale_bar(length: float, unit: str, cm_per_unit: float):
    """Bar of `length` (in `unit`, e.g. 5 and "Å") for a picture in which one unit is
    cm_per_unit cm long on the final page: measure a known distance (a cell edge) in
    the placed picture and divide. The part is exactly that long."""
    if not (length > 0 and cm_per_unit > 0 and math.isfinite(length * cm_per_unit)):
        raise ValueError("length and cm_per_unit must be positive numbers")
    bar = length * cm_per_unit
    if bar > 25:
        raise ValueError(f"the bar would be {bar:.1f} cm long; check cm_per_unit")
    txt = f"{length:g} {unit}"
    w = max(bar + 0.3, len(txt) * 0.2 + 0.3)
    fig, ax = new_part(w, 0.85)
    x0 = (w - bar) / 2
    line(ax, (x0, 0.22), (x0 + bar, 0.22))
    for x in (x0, x0 + bar):
        line(ax, (x, 0.12), (x, 0.32))
    label(ax, w / 2, 0.55, txt, ha="center", va="center")
    fig._pubstyle_bar_cm = bar
    return fig


# ---------------------------------------------------------------- 5. region strips

def region_strip(regions, total_cm: float = 7.0, height_cm: float = 0.55,
                 axis_label: str | None = None, boundary_extra_cm: float = 0.0):
    """Strips side by side with a dashed line at every boundary, for crystal | glass
    interfaces and layered models. regions = [("Crystal", 15.0), ("Glass", 15.0)]
    (name, length in any unit, only the ratios matter); a third item is the grey level
    (0 black .. 1 white). boundary_extra_cm lets the dashed lines reach beyond the strip
    so they can run through a picture or a plot placed above or below. axis_label, if
    given, adds a double arrow underneath with that text, e.g. r"$\\zeta$ (Å)"."""
    if not regions:
        raise ValueError("regions is empty")
    lens = [float(r[1]) for r in regions]
    if min(lens) <= 0:
        raise ValueError("every region needs a positive length")
    greys = [r[2] if len(r) > 2 else (0.93 if i % 2 == 0 else 0.82) for i, r in enumerate(regions)]
    ex = boundary_extra_cm
    below = 0.55 if axis_label else 0.0
    w, h = total_cm + 0.2, height_cm + 2 * ex + 0.1 + below
    fig, ax = new_part(w, h)
    y0 = below + ex + 0.05
    x = 0.1
    xs = [x]
    for (name, *_), ln, g in zip(regions, lens, greys):
        wd = total_cm * ln / sum(lens)
        ax.add_patch(Rectangle((x, y0), wd, height_cm, fc=str(g), ec=INK, lw=ps.DATA_LW, clip_on=False))
        label(ax, x + wd / 2, y0 + height_cm / 2, name, ha="center", va="center")
        x += wd
        xs.append(x)
    for xb in xs[1:-1]:
        line(ax, (xb, y0 - ex), (xb, y0 + height_cm + ex), dashed=True)
    if axis_label:
        arrow(ax, (0.1, 0.2), (0.1 + total_cm, 0.2), both=True)
        label(ax, w / 2, 0.42, axis_label, ha="center", va="center")
    return fig


# ---------------------------------------------------------------- 6. energy level diagram

def level_diagram(columns, ylabel: str = "Energy (eV)", links=(), reg=None):
    """Energy levels, one column per system. columns = [{"name": "Host", "levels":
    [(-6.1, "HOMO"), (-2.3, "LUMO")], "color": key}, ...]; the colour key goes through
    the colour registry (group "series"), default dark grey. links = [(col_a, level_i,
    col_b, level_j), ...] draws dashed lines between levels (indices from 0). It is an
    ordinary framed figure, so the usual checks apply."""
    if not columns:
        raise ValueError("columns is empty")
    reg = reg or ps.ColorRegistry()
    fig, ax = ps.new_figure("standard")
    n = len(columns)
    allv = [lv[0] for c in columns for lv in c["levels"]]
    if not allv:
        raise ValueError("no levels given")
    half = 0.28
    pos = {}
    for i, col in enumerate(columns):
        colour = reg.color(col["color"], "series") if col.get("color") else INK
        for j, (e, name) in enumerate(col["levels"]):
            ax.plot([i + 1 - half, i + 1 + half], [e, e], color=colour, lw=ps.DATA_LW,
                    solid_capstyle="butt")
            pos[(i, j)] = (i + 1, e)
            if name:
                ps.label_point(ax, i + 1 + half, e, name)
    for a, i, b, j in links:
        (xa, ea), (xb, eb) = pos[(a, i)], pos[(b, j)]
        ax.plot([xa + half, xb - half], [ea, eb], color="0.45", lw=ps.DATA_LW, ls=DASH, zorder=0.5)
    span = max(allv) - min(allv) or 1.0
    ax.set_xlim(0.4, n + 0.9)
    ax.set_ylim(min(allv) - 0.15 * span, max(allv) + 0.15 * span)
    ax.set_xticks(range(1, n + 1), [c["name"] for c in columns])
    ax.xaxis.set_minor_locator(mpl.ticker.NullLocator())
    ax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(6, steps=[1, 2, 2.5, 5, 10]))
    ax.set_ylabel(ylabel)
    return fig


# ---------------------------------------------------------------- 7. zoom inset

def add_inset(ax, region, rect, xlabel: str | None = None, ylabel: str | None = None):
    """Zoom inset in an ordinary figure. region = (x0, x1, y0, y1) in data units of ax;
    rect = (x, y, w, h) of the inset as fractions of ax. Draws a dashed box around the
    region and connector lines, and returns the inset axes: plot the same data into it.
    Put it where the curves leave room (the checker reports covered data)."""
    x0, x1, y0, y1 = region
    if not (x0 < x1 and y0 < y1):
        raise ValueError("region must be (x0, x1, y0, y1) with x0 < x1 and y0 < y1")
    if not (0 <= rect[0] and 0 <= rect[1] and rect[0] + rect[2] <= 1 and rect[1] + rect[3] <= 1):
        raise ValueError("rect must lie inside the axes (fractions 0..1)")
    iax = ax.inset_axes(rect)
    iax.set_xlim(x0, x1)
    iax.set_ylim(y0, y1)
    iax.xaxis.set_major_locator(mpl.ticker.MaxNLocator(3))
    iax.yaxis.set_major_locator(mpl.ticker.MaxNLocator(3))
    iax.xaxis.set_minor_locator(mpl.ticker.NullLocator())
    iax.yaxis.set_minor_locator(mpl.ticker.NullLocator())
    if xlabel:
        iax.set_xlabel(xlabel)
    if ylabel:
        iax.set_ylabel(ylabel)
    patch, conns = ax.indicate_inset_zoom(iax, edgecolor="0.45", alpha=1.0)
    for a in [patch, *conns]:
        a.set_linewidth(ps.DATA_LW)
        a.set_linestyle(DASH)
    return iax

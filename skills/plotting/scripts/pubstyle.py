"""Shared figure style for computational materials-science projects (the `plotting` skill).

One copy of this file lives in each project at figures/_style/pubstyle.py
(made by init_figure.py). Every figure's plot.py imports it, so changing the
style here changes every figure of that project on the next redraw.

Typical plot.py (the template made by init_figure.py has this shape):

    import pubstyle as ps

    def draw():                                   # called once per colour mode
        reg = ps.ColorRegistry()                  # figures/_style/colors.json
        fig, ax = ps.new_figure("standard")       # 8 cm x 6 cm
        ax.plot(x, y, color=reg.color("Li"), label="Li")
        ps.nice_limits(ax, y.max())               # axis top: max + 10 %, rounded up
        ps.place_text(ax, "Glass", x_range=(0, 15))  # region name on a free spot
        ps.place_legend(ax)                       # top right unless it covers data or text
        return fig

    # writes output/normal/ and output/soft/ (PNG x2, PDF, SVG, TIFF + checks each)
    ps.save_modes(draw, "003_Li6PS5Cl_bulk_DOS", folder=".")

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
from matplotlib.path import Path as MPath  # noqa: E402
from matplotlib.text import Text  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)
logging.getLogger("fontTools").setLevel(logging.ERROR)     # "FFTM NOT subset" etc. while embedding SVG fonts

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
#   0.8.0: check_figure now audits the real fonts, sizes, weights, line widths,
#          tick directions, grids and frames; SVG files embed a font subset.
#   0.9.0: apply(mode="soft") for a low-saturation look; band/DOS readers take the filled-band count from the EIGENVAL occupations
#          (spin-orbit, odd electron counts), the gap and direct/indirect from all
#          k-points, last E-fermi from OUTCAR; colors.json is locked and written
#          atomically; fake bold is detected; palette 2 (Lancet colours).
#   0.9.1: read_plane() reads Multiwfn plane maps (ELF, density slices); no change
#          to existing functions, so figures drawn with 0.9.0 look the same.
#   0.9.2: read_plane() default unit is Å (what Multiwfn writes) and it reads
#          Multiwfn's six-column file (X Y Z x y value); 0.9.1 assumed Bohr.
STYLE_VERSION = "0.9.2"

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
# so panels line up when they are assembled in an image editor.
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

# Unordered categories (elements, structures, methods). Palette 2 is the Lancet
# set of the ggsci collection (navy, red, green, purple, teal, peach), chosen by
# the project owner for looks. Known limits, so never rely on colour alone: under
# red/green-blind or blue-yellow-blind simulation the closest pairs are only
# about 7 CIEDE2000 apart (teal/purple, red/green), and the peach is pale
# (L* 78), meant for fills and markers. Where curves of similar colour must be
# told apart, add line styles or marker shapes. Palette 1 (red/blue/amber/teal/
# purple/pink) stays for projects that already hold a colors.json; they keep it
# until `init_figure.py --update-style` archives that file.
# Never generate a 7th color: use line styles or marker shapes, or split the figure.
PALETTES = {
    1: ["#C8553D", "#3D6FB6", "#C98A1E", "#2A9D8F", "#6B5BA8", "#D0628E"],
    2: ["#00468B", "#ED0000", "#42B540", "#925E9F", "#0099B4", "#FDAF91"],
}
PALETTE_VERSION = 2      # the palette new projects get; stored in colors.json
CATEGORICAL = PALETTES[PALETTE_VERSION]

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
PREFERRED_BY = {
    1: {"S": "#C98A1E", "Cl": "#2A9D8F", "P": "#6B5BA8", "Li": "#3D6FB6",
        "O": "#C8553D", "Na": "#D0628E", "Br": "#C8553D"},
    2: {"S": "#FDAF91", "Cl": "#42B540", "P": "#925E9F", "Li": "#00468B",
        "O": "#ED0000", "Na": "#0099B4", "Br": "#ED0000"},
}
PREFERRED = PREFERRED_BY[PALETTE_VERSION]

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
        self.palette = PALETTE_VERSION
        self.data = self._load()
        if self.palette != PALETTE_VERSION:
            print(f"NOTE color registry: {self.path} uses the older palette {self.palette}; "
                  f"it stays as it is so existing figures keep their colors. Palette "
                  f"{PALETTE_VERSION} is the new default; run init_figure.py --update-style "
                  "to switch (the old file is archived, figures change colour on redraw).")

    # -- storage ---------------------------------------------------------
    def _load(self) -> dict:
        data = {g: {} for g in GROUPS}
        if not self.path.exists():
            return data
        try:
            stored = json.loads(self.path.read_text(encoding="utf-8") or "{}")
            if not isinstance(stored, dict) or not all(
                    isinstance(d, dict) and all(isinstance(c, str) for c in d.values())
                    for k, d in stored.items() if k != "_palette"):
                raise ValueError("unexpected structure")
        except (ValueError, OSError) as e:
            raise ValueError(
                f"{self.path} is damaged ({e}). It holds the fixed colors of this project; "
                f"restore it from figures/_style/archive/ or from version control. Deleting "
                f"it starts new assignments and can change colors of existing figures, so "
                f"ask the user before doing that.") from None
        for g, d in stored.items():
            if g == "_palette":
                continue
            data.setdefault(g, {}).update(d)
        # a file with colors but without the key predates palette 2
        pal = stored.get("_palette", 1 if any(data.values()) else PALETTE_VERSION)
        if pal not in PALETTES:
            raise ValueError(f"{self.path} was made by a newer pubstyle (palette {pal}); "
                             "update the style copy with init_figure.py --update-style")
        self.palette = pal
        return data

    def _write(self) -> None:
        out = dict(self.data)
        out["_palette"] = self.palette
        tmp = self.path.with_name(f"{self.path.name}.{os.getpid()}.tmp")
        tmp.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp, self.path)                       # atomic: never a half-written file

    class _Lock:
        """Cross-process lock (a lock file made with O_EXCL); several figures
        drawn in parallel must not overwrite each other's new colors."""

        def __init__(self, path: Path, timeout: float = 15.0):
            self.path, self.timeout = path.with_name(path.name + ".lock"), timeout

        def __enter__(self):
            import time
            t0 = time.time()
            while True:
                try:
                    fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    os.close(fd)
                    return self
                except FileExistsError:
                    if time.time() - t0 > self.timeout:
                        try:                              # stale lock of a crashed run
                            if time.time() - self.path.stat().st_mtime > self.timeout:
                                self.path.unlink()
                                continue
                        except FileNotFoundError:
                            continue
                        raise RuntimeError(f"cannot lock the color registry ({self.path}); "
                                           "another figure is writing it, or delete the stale "
                                           "lock file if no plot is running") from None
                    time.sleep(0.05)

        def __exit__(self, *exc):
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass

    def color(self, key: str, group: str = "element") -> str:
        if group not in GROUPS:
            raise ValueError(f"group must be one of {GROUPS}")
        if group == "element":
            key = element_symbol(key)                    # Li_sv -> Li
        if key in self.data[group]:
            return tone(self.data[group][key])
        with self._Lock(self.path):
            self.data = self._load()                     # pick up colors other runs added
            table = self.data[group]
            if key in table:
                return tone(table[key])
            used = set(table.values())
            palette = PALETTES[self.palette]
            free = [c for c in palette if c not in used]
            if not free:
                raise RuntimeError(
                    f"All {len(palette)} colors of group '{group}' are taken; cannot add "
                    f"'{key}'. Distinguish further series by line style or marker, or split "
                    "the figure. Do not invent a new color.")
            pick = PREFERRED_BY[self.palette].get(key) if group == "element" else None
            chosen = pick if pick in free else free[0]
            table[key] = chosen
            self._write()
        print(f"color registry: {group} '{key}' -> {chosen} (new, recorded in {self.path})")
        return tone(chosen)


# ---------------------------------------------------------------- style

MODES = ("normal", "soft")
SOFT_CHROMA = 0.60       # soft mode keeps 60 % of each colour's chroma, same lightness
SOFT_ALPHA_TOP = 0.38    # gradient fills start this strong at the curve (normal: 0.55)

_STATE = {"font": None, "standin": False, "mode": "normal"}


def _to_lab(hexc: str) -> np.ndarray:
    c = np.asarray(to_rgb(hexc))
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = lin @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722],
                          [0.0193, 0.1192, 0.9505]]).T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def _from_lab(lab: np.ndarray) -> str:
    fy = (lab[0] + 16) / 116
    f = np.array([fy + lab[1] / 500, fy, fy - lab[2] / 200])
    xyz = np.where(f ** 3 > 0.008856, f ** 3, (f - 16 / 116) / 7.787) * np.array([0.95047, 1.0, 1.08883])
    lin = np.linalg.inv(np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722],
                                  [0.0193, 0.1192, 0.9505]])) @ xyz
    lin = np.clip(lin, 0, 1)
    c = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    return to_hex(np.clip(c, 0, 1)).upper()


def soften(hexc: str, keep: float = SOFT_CHROMA) -> str:
    """Same hue and lightness, chroma multiplied by `keep` (0 = gray, 1 = unchanged)."""
    lab = _to_lab(hexc)
    return _from_lab(np.array([lab[0], lab[1] * keep, lab[2] * keep]))


def tone(hexc: str) -> str:
    """The colour as drawn in the current mode: unchanged in normal mode, softened
    in soft mode. Use it for any palette colour taken by hand (e.g. CATEGORICAL[0])."""
    return soften(hexc) if _STATE["mode"] == "soft" else hexc


def _face_of(prop):
    """The font FILE matplotlib really resolves for these properties, as the
    font manager's entry (has .name, .weight, .style, .fname)."""
    path = font_manager.findfont(prop)
    for f in font_manager.fontManager.ttflist:
        if f.fname == path:
            return f
    return None


def _face_problem(prop, want_italic: bool = False) -> str | None:
    """Why the resolved font file is not a genuine bold (italic) face, or None.
    Without e.g. arialbd.ttf matplotlib silently draws the REGULAR file while
    the text still says weight=bold; only the file tells the truth."""
    face = _face_of(prop)
    if face is None:
        return "no font file found"
    if _weight_num(face.weight) < 600:
        return f"{Path(face.fname).name} is a regular-weight file, not a bold face"
    if want_italic and face.style not in ("italic", "oblique"):
        return f"{Path(face.fname).name} is not an italic face"
    return None


def _require_real_faces(font: str) -> None:
    for style, want_italic, need in (("normal", False, "bold"), ("italic", True, "bold italic")):
        prop = font_manager.FontProperties(family=font, weight="bold", style=style)
        why = _face_problem(prop, want_italic)
        if why:
            raise RuntimeError(
                f"{font} has no real {need} face ({why}). The style needs genuine bold and "
                f"bold-italic files (for Arial: arialbd.ttf and arialbi.ttf); a regular file "
                f"would be drawn as fake bold. Follow references/setup.md, then delete "
                f"matplotlib's font cache.")


def apply(mode: str = "normal") -> None:
    """Install the style. mode="normal" (default): the palette as it is.
    mode="soft": same hues and lightness at 60 % chroma and lighter gradient fills,
    for a calm look; use it only when the user asks, and keep one mode per paper."""
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
    font, standin = _pick_font()
    _require_real_faces(font)
    _STATE.update(font=font, standin=standin, mode=mode)
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
    cax._pubstyle_colorbar = True          # lets check_figure tell it from the main frame
    cb = fig.colorbar(mappable, cax=cax)
    cb.set_label(label, fontsize=LABEL_PT)
    cb.outline.set_linewidth(FRAME_LW)
    cb.ax.tick_params(direction="out", width=FRAME_LW, length=MAJOR_LEN)
    cb.ax.minorticks_off()
    return cb


# ---------------------------------------------------------------- axis limits

def _nice_step(span: float, max_ticks: int = 6) -> float:
    if not (math.isfinite(span) and span > 0):
        raise ValueError(f"cannot choose tick steps for an axis span of {span!r}")
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
    if not (math.isfinite(data_max) and math.isfinite(data_min)):
        raise ValueError("nice_limits: the data range is not finite (NaN or inf in the data?)")
    if start_at_zero and data_max <= 0:
        raise ValueError(
            f"nice_limits: the data maximum is {data_max:g}, so there is nothing above zero "
            "to draw. For all-zero or negative data pass start_at_zero=False and data_min.")
    lo = 0.0 if start_at_zero else data_min
    span = data_max - lo
    hi_needed = data_max + headroom * span
    lo_needed = lo if start_at_zero else data_min - headroom * span
    if hi_needed - lo_needed <= 0:             # flat data: open a small window around it
        pad = abs(data_max) * 0.05 or 0.5
        hi_needed, lo_needed = data_max + pad, lo - pad
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

def gradient_fill(ax, x, y, color, alpha_top: float | None = None, zorder: float = 1):
    """XPS-style fill under a curve: strong at the curve, fading to clear at 0.
    alpha_top defaults to 0.55 (soft mode 0.38). Draw the curve itself on top with
    ax.plot afterwards."""
    if alpha_top is None:
        alpha_top = SOFT_ALPHA_TOP if _STATE["mode"] == "soft" else 0.55
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
    # NaN gaps split the fill into several polygons: clip to all of them
    clip = MPath.make_compound_path(*poly.get_paths())
    im.set_clip_path(clip, transform=ax.transData)
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
    """Value of one INCAR tag as written (string), or None if absent.

    Understands comments (# and !) and several tags on one line separated by
    ';' (e.g. "ICHAIN = 0 ; LCLIMB = .TRUE."). The first occurrence wins."""
    want = tag.strip().upper()
    text = Path(incar_path).read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        line = re.split(r"[#!]", line, maxsplit=1)[0]
        for part in line.split(";"):
            key, eq, val = part.partition("=")
            if eq and key.strip().upper() == want:
                return val.strip()
    return None


_NO_DEFAULT = object()


def incar_true(incar_path: str | Path, tag: str, default=_NO_DEFAULT) -> bool:
    """True if the INCAR tag is switched on (.TRUE., T, .T., TRUE).

    A tag that is not in the file has no safe answer: VASP defaults differ between
    tags and versions (for LCLIMB, VTST documents disagree). So an absent tag raises
    ValueError unless you pass default=True/False yourself; if you do, say so in the
    figure README."""
    v = incar_value(incar_path, tag)
    if v is None:
        if default is _NO_DEFAULT:
            raise ValueError(
                f"{tag} is not set in {incar_path}. Its default depends on the VASP/VTST "
                f"version, so do not guess: write {tag} into the INCAR copy, or pass "
                "default=True/False and state that assumption in the README.")
        return bool(default)
    return v.strip(".").upper().startswith("T")


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


# ---------------------------------------------------------------- scalar-field slices
#
# A scalar field (ELF, electron density, ...) on a flat slice, exported by
# Multiwfn as plane.txt (main function 4, then "Export the current plane data
# to plane.txt" in the result menu). Multiwfn prints "length unit is in
# Angstrom" when it writes the file, and the columns are: X Y Z (Cartesian
# position of the grid point), x y (position in the graph), value. The reader
# also takes "x y z value" and "x y value". The value is the last column;
# blank lines are ignored.

BOHR_TO_ANG = 0.529177210903


class PlaneMap:
    """A scalar field on a regular rectangular slice. Attributes:
      u, v     (nu,), (nv,) slice axes in Å, both starting at 0 (the graph's x and y
               when the file has them)
      Z        (nv, nu) values; draw with
               ax.imshow(Z, origin="lower", extent=m.extent, ...)
      origin, e1, e2   the slice's 3D frame in Å (grid point (0, 0) and the unit
               vectors along u and v); None when the file had only 2D coordinates
    """

    def __init__(self, u, v, Z, origin=None, e1=None, e2=None):
        self.u, self.v, self.Z = u, v, Z
        self.origin, self.e1, self.e2 = origin, e1, e2

    @property
    def extent(self):
        return (self.u[0], self.u[-1], self.v[0], self.v[-1])

    def project(self, xyz):
        """Atoms of the same structure (N x 3, Å) -> (u, v, h): position on the
        slice and distance from its plane, all in Å. Only for 3D-coordinate files."""
        if self.origin is None:
            raise ValueError("this plane file holds only 2D coordinates, so atoms cannot be "
                             "projected; read their positions off Multiwfn's labelled map "
                             "and write them into the README")
        d = np.atleast_2d(np.asarray(xyz, float)) - self.origin
        return d @ self.e1, d @ self.e2, np.abs(d @ np.cross(self.e1, self.e2))


def read_plane(path: str | Path, unit: str = "angstrom") -> PlaneMap:
    """Read Multiwfn's plane.txt. unit is the length unit of its coordinates:
    "angstrom" (what Multiwfn prints when exporting) or "bohr"; the result is in
    Å. The values (last column) are returned unchanged."""
    scale = {"bohr": BOHR_TO_ANG, "angstrom": 1.0}[unit.lower()]
    rows = []
    for line in Path(path).read_text(errors="replace").splitlines():
        try:
            rows.append([float(t) for t in line.replace("D", "E").split()])
        except ValueError:
            continue                      # header or comment line
    rows = [r for r in rows if r]
    if len(rows) < 4 or len({len(r) for r in rows}) != 1 or len(rows[0]) < 3:
        raise ValueError(f"{path}: expected 3, 4 or 6 columns of numbers "
                         "(x y value / x y z value / X Y Z x y value), one grid point per line")
    a = np.array(rows)
    val, ncol = a[:, -1], a.shape[1]
    xyz = a[:, :3] * scale if ncol >= 4 else None            # 3D position of each point
    if ncol >= 6:
        gxy = a[:, 3:5] * scale                              # position in Multiwfn's graph
    elif ncol == 3:
        gxy = a[:, :2] * scale
    else:                                                    # x y z value: the file order sets the axes
        d0 = xyz[1] - xyz[0]
        step = np.linalg.norm(d0)
        jump = np.flatnonzero(np.linalg.norm(np.diff(xyz, axis=0) - d0, axis=1) > 0.01 * step)
        n1 = jump[0] + 1 if jump.size else len(xyz)         # points per row
        if len(xyz) % n1 or len(xyz) // n1 < 2:
            raise ValueError(f"{path}: cannot split the points into equal rows of a rectangular grid")
        k = np.arange(len(xyz))
        gxy = np.column_stack([(k % n1) * step, (k // n1) * np.linalg.norm(xyz[n1] - xyz[0])])
    xs, ix = np.unique(np.round(gxy[:, 0], 5), return_inverse=True)
    ys, iy = np.unique(np.round(gxy[:, 1], 5), return_inverse=True)
    if len(xs) < 2 or len(ys) < 2 or len(xs) * len(ys) != len(val):
        raise ValueError(f"{path}: the points do not form a complete rectangular grid")
    Z = np.empty((len(ys), len(xs)))
    Z[iy, ix] = val
    u, v = xs - xs[0], ys - ys[0]
    if xyz is None:
        return PlaneMap(u, v, Z)
    G = np.empty((len(ys), len(xs), 3))
    G[iy, ix] = xyz
    origin = G[0, 0]
    e1, e2 = G[0, -1] - origin, G[-1, 0] - origin
    e1, e2 = e1 / np.linalg.norm(e1), e2 / np.linalg.norm(e2)
    rebuilt = origin + u[None, :, None] * e1 + v[:, None, None] * e2
    if abs(e1 @ e2) > 1e-3 or not np.allclose(G, rebuilt, atol=1e-3):
        raise ValueError(f"{path}: the points are not a regular rectangular grid")
    return PlaneMap(u, v, Z, origin, e1, e2)


# ---------------------------------------------------------------- band structures
#
# Reads plain VASP text output, so it works with or without HDF5 and needs no
# extra package: EIGENVAL (energies and k-point weights), POSCAR or CONTCAR
# (lattice, for k distances) and vaspkit's KPATH.in (labels of the path ends).
# PBE line mode and HSE06 "SCF mesh + zero-weight path" (vaspkit 251) both
# work: when zero-weight points exist, only they are drawn.

_GREEK = {"GAMMA": r"\Gamma", "DELTA": r"\Delta", "LAMBDA": r"\Lambda",
          "SIGMA": r"\Sigma", "PI": r"\Pi"}


def kpoint_label(raw: str) -> str:
    """vaspkit label -> axis label: GAMMA -> Γ, X_1 -> X with subscript 1."""
    s = raw.strip().lstrip("!").strip()
    base, _, sub = s.partition("_")
    head = _GREEK.get(base.upper())
    head = rf"\rm{head}" if head else rf"\rm {base}"
    return rf"${head}_{{\rm {sub}}}$" if sub else rf"${head}$"


def read_kpath(path: str | Path) -> list[tuple[np.ndarray, str]]:
    """(fractional coordinate, raw label) of every labeled point in vaspkit's
    KPATH.in or a line-mode KPOINTS file."""
    out = []
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    for line in lines[4:]:
        tok = line.replace("!", " ").split()
        if len(tok) >= 4:
            try:
                out.append((np.array([float(t) for t in tok[:3]]), tok[3]))
            except ValueError:
                pass
    if not out:
        raise ValueError(f"{path}: no labeled k-points found")
    return out


def _reciprocal(poscar: str | Path) -> np.ndarray:
    """Reciprocal lattice rows (1/Å, without 2π) from POSCAR/CONTCAR."""
    lines = Path(poscar).read_text(encoding="utf-8", errors="replace").splitlines()
    scale = float(lines[1].split()[0])
    a = np.array([[float(x) for x in lines[i].split()[:3]] for i in (2, 3, 4)])
    if scale < 0:                                   # negative = target volume
        scale = (-scale / abs(np.linalg.det(a))) ** (1 / 3)
    return np.linalg.inv(a * scale).T


def _read_eigenval(path: str | Path):
    tok = Path(path).read_text(encoding="utf-8", errors="replace").split("\n")
    ispin = int(tok[0].split()[3])
    nelect, nk, nb = (int(float(x)) for x in tok[5].split()[:3])
    nums = " ".join(tok[6:]).split()
    per_band = 3 if ispin == 1 else 5
    kpts, wts = np.zeros((nk, 3)), np.zeros(nk)
    eig = np.zeros((ispin, nk, nb))
    occ = np.zeros((ispin, nk, nb))
    i = 0
    for k in range(nk):
        kpts[k] = [float(x) for x in nums[i:i + 3]]
        wts[k] = float(nums[i + 3])
        i += 4
        for b in range(nb):
            row = nums[i:i + per_band]
            eig[0, k, b] = float(row[1])
            if ispin == 2:
                eig[1, k, b] = float(row[2])
                occ[0, k, b], occ[1, k, b] = float(row[3]), float(row[4])
            else:
                occ[0, k, b] = float(row[2])
            i += per_band
    if occ.max() > 1.5:                 # some versions write 2 per filled band
        occ = occ / 2.0
    return nelect, kpts, wts, eig, occ


def _occupied_bands(nelect: int, wts: np.ndarray, occ: np.ndarray):
    """Number of completely filled bands, taken from the OCCUPATIONS in EIGENVAL
    (they are right for ISPIN=1, spin-orbit coupling, and any electron count),
    not from NELECT/2. Returns None when a band is partially filled (metal).
    Only k-points with non-zero weight are used: the zero-weight path points of
    a hybrid band calculation carry no occupations of their own."""
    idx = np.where(wts > 0)[0]
    if len(idx) == 0:
        idx = np.arange(len(wts))
    o = occ[0, idx]
    if np.any((o > 0.02) & (o < 0.98)):
        return None                                  # fractional occupation: metal
    filled = (o > 0.5).sum(axis=1)
    if filled.min() != filled.max():
        return None                                  # the filling changes with k: metal
    nocc = int(filled[0])
    per_band = nelect / nocc if nocc else float("inf")
    if abs(per_band - 2) > 1e-6 and abs(per_band - 1) > 1e-6:
        raise ValueError(
            f"EIGENVAL has {nocc} filled bands for NELECT = {nelect}: that is neither 2 "
            "electrons per band (normal) nor 1 (spin-orbit coupling). An odd electron count "
            "with ISPIN = 1 cannot be an insulator; check ISPIN/MAGMOM and rerun")
    return nocc


def _band_edges(nelect, wts, eig, occ, what="EIGENVAL"):
    """(nocc, v, c) with v, c = top filled / bottom empty band at every k-point,
    or None for a metal (partly filled band, or valence and conduction bands
    overlapping at some k)."""
    nocc = _occupied_bands(nelect, wts, occ)
    if nocc is None:
        return None
    if nocc == 0:
        raise ValueError(f"{what}: no filled band")
    if nocc >= eig.shape[2]:
        raise ValueError(f"{what} has no empty band (NBANDS is too small), so the gap cannot "
                         "be located; rerun with more bands")
    v, c = eig[0, :, nocc - 1], eig[0, :, nocc]
    if c.min() <= v.max():
        return None
    return nocc, v, c


def _is_direct(v: np.ndarray, c: np.ndarray, tol: float = 2e-3) -> bool:
    """Direct gap = ONE k-point holds both band edges (within tol eV, so that
    degenerate or symmetry-equivalent points count, e.g. U and K of fcc).
    Comparing positions along the path is not enough."""
    return bool(np.any((v >= v.max() - tol) & (c <= c.min() + tol)))


def _last_efermi(path: Path):
    """E-fermi of the LAST ionic step / electronic run in an OUTCAR, or None."""
    if not path.exists():
        return None
    m = re.findall(r"E-fermi\s*:\s*(-?[\d.]+)", path.read_text(errors="replace"))
    return float(m[-1]) if m else None


class Bands:
    """Band structure along the path, energies already relative to the zero
    (VBM for insulators, Fermi level for metals). Attributes:
      x        (nk,) distance along the path (1/Å), path breaks add nothing
      energy   (nspin, nk, nbands) in eV, relative to the zero
      ticks    x of each high-symmetry point;  labels  their axis labels
      metal    True if bands cross the Fermi level
      vbm, cbm (x, E) of the band edges on the path (None for metals, and None
               when an edge lies off the drawn path, see off_path)
      gap      the real gap over ALL k-points in EIGENVAL (SCF mesh included);
               gap_path the gap of the drawn path alone
      direct   one k-point holds both edges (all k-points)
      off_path a band edge is not on the drawn path
      zero_eV (absolute energy of the zero), source (str)
    """


def read_bands(folder: str | Path = ".", eigenval: str = "EIGENVAL",
               poscar: str = "POSCAR", kpath: str = "KPATH.in",
               outcar: str = "OUTCAR") -> Bands:
    """Read a band calculation from copies of EIGENVAL, POSCAR (or CONTCAR) and
    KPATH.in in `folder`. OUTCAR is only needed for metals (E-fermi)."""
    folder = Path(folder)
    nelect, kpts, wts, eig, occ = _read_eigenval(folder / eigenval)
    p = folder / poscar
    if not p.exists() and (folder / "CONTCAR").exists():
        p = folder / "CONTCAR"
    rec = _reciprocal(p)
    labeled = read_kpath(folder / kpath)

    zero_w = wts == 0
    hybrid = bool(zero_w.any() and (~zero_w).any())
    path_k, path_e = (kpts[zero_w], eig[:, zero_w]) if hybrid else (kpts, eig)

    # split the path into straight, evenly spaced segments; each segment holds
    # both of its end points (vaspkit and VASP line mode both write them).
    segs, i, n = [], 0, len(path_k)
    while i < n:
        j = i + 1
        if j < n:
            step = path_k[j] - path_k[i]
            while j + 1 < n and np.allclose(path_k[j + 1] - path_k[j], step, atol=1e-5):
                j += 1
        segs.append((i, min(j, n - 1)))
        i = j + 1

    def name(frac):
        for c, lab in labeled:
            if np.allclose(c, frac, atol=1e-4):
                return lab
        raise ValueError(f"k-point {frac} is a path end but has no label in {kpath}")

    x = np.zeros(n)
    ticks, labels, pos = [0.0], [kpoint_label(name(path_k[segs[0][0]]))], 0.0
    for s, (a, b) in enumerate(segs):
        cart = path_k[a:b + 1] @ rec
        d = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(cart, axis=0), axis=1))])
        x[a:b + 1] = pos + d
        pos += d[-1]
        end = kpoint_label(name(path_k[b]))
        if s + 1 < len(segs):
            nxt = kpoint_label(name(path_k[segs[s + 1][0]]))
            if not np.allclose(path_k[b], path_k[segs[s + 1][0]], atol=1e-5):
                end = f"{end}|{nxt}"                    # path break, e.g. U|K
        ticks.append(float(pos))
        labels.append(end)
    # labels joined with "|" are two math strings; merge into one
    labels = [lab.replace("$|$", "|") for lab in labels]

    if eig.shape[0] == 2:
        raise ValueError("ISPIN=2 band structures are not supported yet; ask the user")
    out = Bands()
    out.x, out.ticks, out.labels = x, ticks, labels
    out.source = f"{eigenval}, {p.name}, {kpath}" + (
        " (HSE-type: zero-weight path points only)" if hybrid else "")
    out.hybrid = hybrid
    edges = _band_edges(nelect, wts, eig, occ, eigenval)
    out.metal = edges is None
    out.off_path = False
    if edges is None:
        ef = _last_efermi(folder / outcar)
        if ef is None:
            raise ValueError(f"the bands cross the Fermi level (metal), so the zero is E-fermi: "
                             f"copy the calculation's {outcar} into {folder} as well")
        out.zero_eV = ef
        out.vbm = out.cbm = out.gap = out.gap_path = out.direct = None
    else:
        nocc, v_all, c_all = edges                    # every k-point, SCF mesh included
        out.nocc = nocc
        out.zero_eV = float(v_all.max())
        out.gap = float(c_all.min() - v_all.max())    # the real gap, whatever the path
        out.direct = _is_direct(v_all, c_all)
        v, c = path_e[0, :, nocc - 1], path_e[0, :, nocc]
        out.gap_path = float(c.min() - v.max())
        tol = 2e-3
        out.off_path = bool(v.max() < v_all.max() - tol or c.min() > c_all.min() + tol)
        if out.off_path:
            out.vbm = out.cbm = None                  # edges not on the drawn path: no markers
        else:
            both = np.where((v >= v.max() - tol) & (c <= c.min() + tol))[0]
            iv = ic = int(both[0]) if len(both) else None
            if iv is None:
                iv, ic = int(np.argmax(v)), int(np.argmin(c))
            out.vbm = (x[iv], v[iv] - out.zero_eV)
            out.cbm = (x[ic], c[ic] - out.zero_eV)
    out.energy = path_e - out.zero_eV
    return out


def band_energy_range(bands: Bands, above_cbm: float = 3.0, group_gap: float = 1.0):
    """Default energy window: from just below the bottom of the valence-band
    group touching the VBM (bands separated by > group_gap eV start a new
    group) to about 3 eV above the CBM, both rounded to whole eV."""
    e = bands.energy[0]
    lows = sorted(((e[:, b].min(), e[:, b].max()) for b in range(e.shape[1])
                   if e[:, b].max() <= 1e-6), key=lambda t: -t[1])
    bottom = 0.0
    for lo, hi in lows:
        if hi < bottom - group_gap:
            break
        bottom = min(bottom, lo)
    lo = math.floor(bottom - 0.5)
    up = (bands.gap if bands.gap is not None else 0.0) + above_cbm   # CBM relative to the VBM
    return float(lo), float(math.ceil(up))


def plot_bands(ax, bands: Bands, ylim=None, mark_gap: bool = True):
    """Draw a band structure by the skill's rules on a 'tall' canvas and return
    the y limits (use the same ones for the DOS strip)."""
    lo, hi = ylim or band_energy_range(bands)
    styles = ["-", "--"]
    for s in range(bands.energy.shape[0]):
        for b in range(bands.energy.shape[2]):
            ax.plot(bands.x, bands.energy[s, :, b], color="0.15", lw=DATA_LW, ls=styles[s])
    for t in bands.ticks[1:-1]:
        ax.axvline(t, color="0.6", lw=FRAME_LW, zorder=0.4, gid="reference")
    ax.axhline(0, **REFERENCE_LINE)
    ax.set_xlim(bands.ticks[0], bands.ticks[-1])
    ax.set_xticks(bands.ticks, bands.labels)
    ax.xaxis.set_minor_locator(mpl.ticker.NullLocator())
    ax.set_ylim(lo, hi)
    step = _nice_step(hi - lo, max_ticks=7)
    ax.yaxis.set_major_locator(mpl.ticker.MultipleLocator(step))
    ax.yaxis.set_minor_locator(mpl.ticker.AutoMinorLocator(2))
    ax.set_ylabel(r"$E-E_{\rm F}$ (eV)" if bands.metal else r"$E-E_{\rm VBM}$ (eV)")
    if mark_gap and not bands.metal and bands.vbm is not None:
        (xv, ev), (xc, ec) = bands.vbm, bands.cbm
        ax.plot([xv], [ev], "o", color=tone(CATEGORICAL[1]), ms=MARKER_SIZE, mew=0,
                clip_on=False, zorder=3)
        ax.plot([xc], [ec], "o", color=tone(CATEGORICAL[0]), ms=MARKER_SIZE, mew=0,
                clip_on=False, zorder=3)
        # arrow at the CBM: from E = 0 (VBM level) up to the CBM
        ax.annotate("", xy=(xc, ec), xytext=(xc, ev),
                    arrowprops=dict(arrowstyle="<->", lw=DATA_LW, color="0.15",
                                    shrinkA=0, shrinkB=MARKER_SIZE / 2))
        kind = "direct" if bands.direct else "indirect"
        label_point(ax, xc, (ev + ec) / 2, f"{bands.gap:.2f} eV ({kind})")
    return lo, hi


def bands_summary(bands: Bands) -> str:
    """Lines for the figure README."""
    if bands.metal:
        return (f"- Data: {bands.source}\n- Metal: zero = E-fermi from OUTCAR "
                f"({bands.zero_eV:.4f} eV, last E-fermi in the file; take it from the SCF run "
                "that made the charge density, a non-self-consistent band run can shift it)\n")
    s = (f"- Data: {bands.source}\n"
         f"- Zero: VBM = {bands.zero_eV:.4f} eV (highest occupied band, band "
         f"{bands.nocc}, over all k-points)\n"
         f"- Gap (all k-points in EIGENVAL): {bands.gap:.3f} eV, "
         f"{'direct' if bands.direct else 'indirect'} (direct = one k-point holds both edges)\n")
    if bands.off_path:
        s += (f"- Note: a band edge lies off the drawn path (gap on the path alone: "
              f"{bands.gap_path:.3f} eV); the figure carries no gap marker\n")
    return s


# ---------------------------------------------------------------- DOS
#
# Reads DOSCAR (+ POSCAR/CONTCAR for the element names and counts, EIGENVAL for
# the band edges). Plain text only, same as read_bands.

class Dos:
    """Density of states, energies relative to the zero, DOS per formula unit.
      energy   (n,) eV relative to the zero
      total    (nspin, n) states/eV/f.u.  (spin down is NOT negated here)
      elements {symbol: (nspin, n)} summed over that element's atoms, or {}
      orbitals {symbol: {"s": .., "p": .., "d": ..}} (LORBIT 10/11 only), or {}
      metal, vbm/cbm (eV, relative to the zero; None for metals), gap,
      zero_eV (absolute energy of the zero), formula_units, nspin, source
    """


def element_symbol(name: str) -> str:
    """Element symbol from a VASP/POTCAR name: Li_sv -> Li, Zn_2 -> Zn, Li -> Li.
    Anything that does not look like such a name is returned unchanged."""
    m = re.fullmatch(r"([A-Z][a-z]?)(?:[_/.-]\w*)?", name.strip())
    return m.group(1) if m else name.strip()


def _atom_symbols(poscar: Path) -> list[str]:
    lines = poscar.read_text(encoding="utf-8", errors="replace").splitlines()
    names, counts = lines[5].split(), lines[6].split()
    if not all(c.isdigit() for c in counts):
        raise ValueError(f"{poscar.name}: no element names in line 6 (VASP 4 format)")
    return [element_symbol(n) for n, c in zip(names, counts) for _ in range(int(c))]


def _group_orbitals(cols: np.ndarray, nspin: int) -> dict[str, np.ndarray]:
    """cols: (n, ncols-1) partial DOS columns of one atom -> s/p/d/f, each (nspin, n)."""
    norb = cols.shape[1] // nspin
    sizes = {1: ["s"], 3: ["s", "p", "d"], 4: ["s", "p", "d", "f"],
             9: ["s"] + ["p"] * 3 + ["d"] * 5,
             16: ["s"] + ["p"] * 3 + ["d"] * 5 + ["f"] * 7}.get(norb)
    if sizes is None:
        raise ValueError(f"unexpected number of orbital columns: {norb}")
    out = {}
    for s in range(nspin):
        block = cols[:, s::nspin]               # spin up/down alternate in DOSCAR
        for i, o in enumerate(sizes):
            out.setdefault(o, np.zeros((nspin, cols.shape[0])))[s] += block[:, i]
    return out


def read_dos(folder: str | Path = ".", formula_units: float | None = None,
             doscar: str = "DOSCAR", poscar: str = "POSCAR",
             eigenval: str = "EIGENVAL", outcar: str = "OUTCAR",
             assume_metal: bool = False) -> Dos:
    """Read a DOS calculation from copies of DOSCAR, POSCAR (or CONTCAR) and
    EIGENVAL in `folder`. formula_units is how many formula units the cell holds
    (Li6PS5Cl cell with 4 formula units -> 4); it must be given, the DOS is
    divided by it. Zero: VBM from EIGENVAL for insulators, E-fermi from DOSCAR
    for metals. Without EIGENVAL an insulator cannot be told from a metal, so the
    function stops; pass assume_metal=True only for a system you know is metallic
    (zero = E-fermi, no gap)."""
    if not formula_units or formula_units <= 0:
        raise ValueError("formula_units is required (number of formula units in the "
                         "cell); write the value into the figure README")
    folder = Path(folder)
    lines = (folder / doscar).read_text(encoding="utf-8", errors="replace").splitlines()
    natoms = int(lines[0].split()[0])
    head = lines[5].split()
    nedos, efermi = int(head[2]), float(head[3])
    block = lambda start: np.array(  # noqa: E731
        [[float(x) for x in l.split()] for l in lines[start:start + nedos]])
    tot = block(6)
    energy = tot[:, 0]
    nspin = 2 if tot.shape[1] in (5,) else 1
    total = tot[:, 1:1 + nspin].T / formula_units

    p = folder / poscar
    if not p.exists() and (folder / "CONTCAR").exists():
        p = folder / "CONTCAR"
    elements, orbitals = {}, {}
    if len(lines) >= 6 + (nedos + 1) * (natoms + 1) - 1 and natoms > 0:
        symbols = _atom_symbols(p)
        if len(symbols) != natoms:
            raise ValueError("POSCAR and DOSCAR disagree on the number of atoms")
        for i, sym in enumerate(symbols):
            part = block(6 + (nedos + 1) * (i + 1))[:, 1:]
            grouped = _group_orbitals(part, nspin)
            tot_atom = sum(grouped.values())
            elements[sym] = elements.get(sym, 0) + tot_atom / formula_units
            od = orbitals.setdefault(sym, {})
            for o, v in grouped.items():
                od[o] = od.get(o, 0) + v / formula_units

    out = Dos()
    out.nspin, out.formula_units = nspin, formula_units
    out.total = total
    out.elements, out.orbitals = elements, orbitals
    out.source = f"{doscar}, {p.name}, {eigenval}"
    ev = folder / eigenval
    metal, vbm_abs, cbm_abs = True, None, None
    if nspin == 2:
        raise ValueError("ISPIN=2 DOS: zero must be chosen by hand for now; ask the user")
    if ev.exists():
        nelect, _k, wts, eig, occ = _read_eigenval(ev)
        edges = _band_edges(nelect, wts, eig, occ, eigenval)
        if edges is not None:
            metal = False
            _n, v_all, c_all = edges
            vbm_abs, cbm_abs = v_all.max(), c_all.min()
    elif not assume_metal:
        raise FileNotFoundError(
            f"{ev} not found. The zero (VBM for an insulator, E-fermi for a metal) and the "
            f"gap come from EIGENVAL: copy it into {folder}. For a system you know is "
            "metallic you may pass assume_metal=True.")
    out.metal = bool(metal)
    out.zero_eV = float(efermi) if metal else float(vbm_abs)
    out.energy = energy - out.zero_eV
    out.vbm = None if metal else 0.0
    out.cbm = None if metal else float(cbm_abs - vbm_abs)
    out.gap = out.cbm
    return out


def dos_energy_range(dos: Dos, above_cbm: float = 3.0, group_gap: float = 1.0):
    """Default window: from just below the lowest DOS feature that belongs to the
    valence-band group touching the VBM (features separated by more than
    group_gap eV of empty DOS start a new group) up to about 3 eV above the CBM,
    both rounded to whole eV. Metals: 6 eV below and above E_F."""
    if dos.metal:
        return -6.0, 6.0
    t = dos.total.sum(axis=0)
    occ = dos.energy <= 1e-6
    on = occ & (t > 0.01 * t[occ].max())
    e = dos.energy
    bottom = 0.0
    for i in np.where(on)[0][::-1]:
        if e[i] < bottom - group_gap:
            break
        bottom = min(bottom, e[i])
    return float(math.floor(bottom - 0.5)), float(math.ceil(dos.cbm + above_cbm))


def plot_dos(ax, dos: Dos, reg: "ColorRegistry", xlim=None, kind="elements",
             fill: str = "gradient", total: bool = True, mark_gap: bool = True):
    """Draw a DOS by the skill's rules on a 'standard' canvas: energy on x,
    total as light grey fill, one line per element (kind="elements"), total only (kind="total") or per
    orbital of the elements given in `kind` as {"S": ["p"], ...}; gradient fill;
    gap arrow. Returns (xlim, ymax). Add the legend yourself with
    ps.place_legend(ax) after any extra labels."""
    lo, hi = xlim or dos_energy_range(dos)
    sel = (dos.energy >= lo) & (dos.energy <= hi)
    if not sel.any():
        raise ValueError(f"no DOS points between {lo:g} and {hi:g} eV (relative to the zero); "
                         "check xlim")
    if kind == "total" and not total:
        raise ValueError('nothing to draw: kind="total" needs total=True')
    e = dos.energy
    spin_sign = [1.0, -1.0][:dos.nspin]
    curves = []
    if kind == "total":
        pass
    elif kind == "elements":
        if not dos.elements:
            raise ValueError("DOSCAR has no per-atom DOS; run with LORBIT = 11 (or 10)")
        curves = [(sym, None, v, reg.color(sym)) for sym, v in dos.elements.items()]
    else:
        if not dos.orbitals:
            raise ValueError("DOSCAR has no per-atom DOS; run with LORBIT = 11 (or 10)")
        for sym, orbs in kind.items():
            for o in orbs:
                curves.append((f"{sym} {o}", None, dos.orbitals[sym][o],
                               reg.color(f"{sym} {o}", "series")))
    ymax = 0.0
    if total:
        for s, sg in enumerate(spin_sign):
            y = sg * dos.total[s]
            ax.fill_between(e, y, color="0.85", lw=0, zorder=0.8,
                            label="Total" if s == 0 else None)
        ymax = max(ymax, dos.total[:, sel].max())
    for name, _, v, c in curves:
        for s, sg in enumerate(spin_sign):
            y = sg * v[s]
            if fill == "gradient":
                gradient_fill(ax, e, y, c)
            elif fill == "translucent":
                ax.fill_between(e, y, color=c, alpha=0.3, lw=0, zorder=1)
            ax.plot(e, y, color=c, label=name if s == 0 else None, zorder=2)
        ymax = max(ymax, v[:, sel].max())
    ax.axvline(0, **REFERENCE_LINE)
    ax.set_xlim(lo, hi)
    ax.xaxis.set_major_locator(mpl.ticker.MultipleLocator(_nice_step(hi - lo, 7)))
    if dos.nspin == 2:
        nice_limits(ax, ymax, start_at_zero=True)
        top = ax.get_ylim()[1]
        ax.set_ylim(-top, top)
    else:
        nice_limits(ax, ymax)
    ax.set_xlabel(r"$E-E_{\rm F}$ (eV)" if dos.metal else r"$E-E_{\rm VBM}$ (eV)")
    ax.set_ylabel("DOS (states/eV/f.u.)")
    if mark_gap and not dos.metal and dos.gap is not None and dos.cbm <= hi:
        top = ax.get_ylim()[1]
        yarrow = 0.12 * top
        ax.annotate("", xy=(dos.cbm, yarrow), xytext=(0.0, yarrow),
                    arrowprops=dict(arrowstyle="<->", lw=DATA_LW, color="0.15",
                                    shrinkA=0, shrinkB=0))
        place_text(ax, f"{dos.gap:.2f} eV", x_range=(max(lo, -1.5), min(hi, dos.cbm + 1.5)),
                   y_range=(yarrow, 0.6 * top), prefer="bottom")
    return (lo, hi), ymax


def dos_summary(dos: Dos) -> str:
    """Lines for the figure README."""
    s = (f"- Data: {dos.source}\n- DOS divided by {dos.formula_units:g} formula unit(s) "
         "of the cell; no extra smoothing (broadening is the one used in the VASP run)\n")
    s += ("- Element/orbital curves are projections onto spheres around the atoms (RWIGS); "
          "they do not add up to the total DOS\n")
    if dos.metal:
        s += f"- Metal: zero = E-fermi ({dos.zero_eV:.4f} eV, from DOSCAR)\n"
    else:
        s += (f"- Zero: VBM = {dos.zero_eV:.4f} eV (from EIGENVAL, all k-points)\n"
              f"- Gap: {dos.gap:.3f} eV (EIGENVAL k-points, not the DOS edge)\n")
    s += "- Per-atom DOS: " + (", ".join(dos.elements) if dos.elements else "none (LORBIT = 0)") + "\n"
    return s


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
        if getattr(ax, "_pubstyle_part", False):      # labels on arrows and boxes are meant to touch
            continue
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


def _weight_num(w) -> int:
    if isinstance(w, (int, float)):
        return int(w)
    return int(font_manager.weight_dict.get(str(w), 400))


def _all_axes(fig) -> list:
    """Every axes of the figure, including child axes (the top axis of an Arrhenius plot)."""
    out, seen = [], set()

    def walk(ax):
        if id(ax) in seen:
            return
        seen.add(id(ax))
        out.append(ax)
        for child in ax.child_axes:
            walk(child)

    for ax in fig.axes:
        walk(ax)
    return out


def _audit_style(fig) -> dict[str, list[str]]:
    """Measure what is really on the figure (not what apply() was asked to do):
    font family and weight of every text, font sizes by role, line widths,
    tick direction/width/length, grids, frame. Needs a drawn figure so tick
    labels exist. Returns {topic: [problem, ...]}; an empty list means fine."""
    font = _STATE["font"]
    bad = {"font": [], "size": [], "weight": [], "line": [], "axes": []}

    def text(t, want_pt, what):
        s = t.get_text()
        if not s or not t.get_visible():
            return
        who = f"{what} '{s[:24]}'"
        if t.get_fontname() != font:
            bad["font"].append(f"{who} is set in {t.get_fontname()}")
        if abs(t.get_fontsize() - want_pt) > 0.05:
            bad["size"].append(f"{who} is {t.get_fontsize():g} pt, must be {want_pt:g} pt")
        if _weight_num(t.get_fontweight()) < 700:
            bad["weight"].append(f"{who} is not bold")
        else:
            why = _face_problem(t.get_fontproperties(), t.get_fontstyle() in ("italic", "oblique"))
            if why:
                bad["weight"].append(f"{who}: {why} (fake bold)")

    for key in ("mathtext.rm", "mathtext.it", "mathtext.bf", "mathtext.sf", "mathtext.cal"):
        if not str(mpl.rcParams[key]).startswith(font):
            bad["font"].append(f"{key} is {mpl.rcParams[key]!r}, formulas must use {font}")
        else:
            prop = font_manager.FontProperties(mpl.rcParams[key])
            why = _face_problem(prop, "italic" in str(mpl.rcParams[key]))
            if why:
                bad["weight"].append(f"formulas ({key}): {why} (fake bold)")

    children = {id(c) for ax in fig.axes for c in ax.child_axes}
    for ax in _all_axes(fig):
        is_colorbar = getattr(ax, "_pubstyle_colorbar", False)
        for axis, nm in ((ax.xaxis, "x"), (ax.yaxis, "y")):
            for t in axis.get_majorticklabels() + axis.get_minorticklabels():
                text(t, TICK_PT, f"{nm} tick label")
            text(axis.label, LABEL_PT, f"{nm} axis title")
            # read the tick objects themselves: get_tick_params() only reports values
            # that were set explicitly, not the ones that came from rcParams
            for which, ticks, want_len in (("major", axis.get_major_ticks(), MAJOR_LEN),
                                           ("minor", axis.get_minor_ticks(), MINOR_LEN)):
                for tk in ticks:
                    direction = getattr(tk, "_tickdir", None)
                    if direction not in (None, "out"):
                        bad["axes"].append(f"{nm} {which} ticks point {direction}, must point out")
                    mark = tk.tick1line if tk.tick1line.get_visible() else tk.tick2line
                    if not mark.get_visible():
                        continue
                    if abs(mark.get_markeredgewidth() - FRAME_LW) > 0.01:
                        bad["axes"].append(f"{nm} {which} tick width is "
                                           f"{mark.get_markeredgewidth():g} pt, must be {FRAME_LW:g} pt")
                    if abs(mark.get_markersize() - want_len) > 0.01:
                        bad["axes"].append(f"{nm} {which} tick length is "
                                           f"{mark.get_markersize():g} pt, must be {want_len:g} pt")
            if any(tk.gridline.get_visible()
                   for tk in axis.get_major_ticks() + axis.get_minor_ticks()):
                bad["axes"].append(f"{nm} axis has grid lines (no grids allowed)")
        if not is_colorbar and id(ax) not in children:
            for side, sp in ax.spines.items():
                if not sp.get_visible():
                    bad["axes"].append(f"frame side '{side}' is hidden (the frame must be closed)")
                elif abs(sp.get_linewidth() - FRAME_LW) > 0.01:
                    bad["axes"].append(f"frame side '{side}' is {sp.get_linewidth():g} pt, must be {FRAME_LW:g} pt")
        for t in ax.texts:
            text(t, ANNOT_PT, "text")
        leg = ax.get_legend()
        if leg is not None:
            for t in leg.get_texts():
                text(t, LEGEND_PT, "legend text")
        for ln in ax.get_lines():
            if ln.get_visible() and _is_visible_style(ln.get_linestyle()) \
                    and abs(ln.get_linewidth() - DATA_LW) > 0.01:
                bad["line"].append(f"line '{ln.get_label()}' is {ln.get_linewidth():g} pt, "
                                   f"must be {DATA_LW:g} pt")
        if getattr(ax, "_pubstyle_part", False):          # free layouts (pubparts): patches, arrows
            for pa in ax.patches:
                if pa.get_visible() and pa.get_edgecolor()[3] > 0 and pa.get_linewidth() > 0 \
                        and abs(pa.get_linewidth() - DATA_LW) > 0.01:
                    bad["line"].append(f"{type(pa).__name__} outline is {pa.get_linewidth():g} pt, "
                                       f"must be {DATA_LW:g} pt")
            for tx in ax.texts:
                ap = getattr(tx, "arrow_patch", None)
                if ap is not None and abs(ap.get_linewidth() - DATA_LW) > 0.01:
                    bad["line"].append(f"arrow is {ap.get_linewidth():g} pt, must be {DATA_LW:g} pt")
        for coll in ([] if is_colorbar else ax.collections):    # colorbar dividers are not data lines
            if type(coll).__name__ == "LineCollection" and coll.get_visible():
                widths = [w for w in np.atleast_1d(coll.get_linewidths()) if w > 0]
                if any(abs(w - DATA_LW) > 0.01 for w in widths):
                    bad["line"].append(f"line collection (error bars?) is {max(widths):g} pt, "
                                       f"must be {DATA_LW:g} pt")
    for t in fig.texts:
        text(t, ANNOT_PT, "figure text")
    return bad


def _fmt_problems(items: list[str], limit: int = 5) -> str:
    items = list(dict.fromkeys(items))               # drop exact repeats, keep order
    more = f"; +{len(items) - limit} more" if len(items) > limit else ""
    return "; ".join(items[:limit]) + more


def check_figure(fig) -> list[str]:
    """Return lines 'PASS ...' / 'FAIL ...' / 'NOTE ...'."""
    out = []
    font = _STATE["font"]
    fig.canvas.draw()                                # tick labels exist only after a draw
    audit = _audit_style(fig)
    out.append(f"NOTE style: pubstyle {STYLE_VERSION}, colour mode {_STATE['mode']}")
    if any(getattr(ax, "_pubstyle_part", False) for ax in fig.axes):
        out.append("NOTE part: free layout (pubparts); fonts, sizes, line widths and the canvas "
                   "edge are checked, label overlap is not")
    if _STATE["standin"]:
        out.append(f"NOTE font: {font} used as a DRAFT stand-in for Arial; "
                   "redraw on a machine with Arial")
    out.append("FAIL font: " + _fmt_problems(audit["font"]) if audit["font"]
               else (f"PASS font: every text and formula is set in {font}"
                     if not _STATE["standin"] else "PASS font: every text and formula uses the one font"))
    out.append("FAIL text size: " + _fmt_problems(audit["size"]) if audit["size"]
               else f"PASS text size: axis titles {LABEL_PT} pt, ticks {TICK_PT} pt, "
                    f"legend {LEGEND_PT} pt, labels {ANNOT_PT} pt")
    out.append("FAIL text weight: " + _fmt_problems(audit["weight"]) if audit["weight"]
               else "PASS text weight: all text is bold")
    out.append("FAIL line width: " + _fmt_problems(audit["line"]) if audit["line"]
               else f"PASS line width: all lines are {DATA_LW:g} pt")
    out.append("FAIL axes: " + _fmt_problems(audit["axes"]) if audit["axes"]
               else "PASS axes: closed frame, ticks out, no grid, tick sizes as specified")

    bad = []
    for t, s in _texts(fig):
        if _UNICODE_SCRIPTS & set(s):
            bad.append(s)
        plain = re.sub(r"\$[^$]*\$", "", s)
        if "^" in plain or "_" in plain:
            bad.append(s)
    out.append("FAIL text: Unicode or plain-text super/subscripts / underscores in " + repr(bad)
               + ' -> write them as math, e.g. r"Na$_{\\rm 3}$PS$_{\\rm 4}$"; a VASP name such '
               'as Li_sv is the POTCAR variant, label the element "Li"'
               if bad else "PASS text: super/subscripts are rendered as math")

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


def _embed_svg_fonts(path: Path) -> str:
    """matplotlib writes SVG text as real <text> (editable) but only names the font.
    Add the glyphs the figure uses as an @font-face subset (base64 TrueType), so a
    browser shows the SVG in the right font on any machine. Returns a check line.
    Inkscape and Illustrator ignore embedded web fonts; there Arial must be installed."""
    import base64
    import html
    try:
        from fontTools import subset
    except ImportError:
        return "NOTE svg: fontTools not installed; fonts are named in the SVG but not embedded"
    text = path.read_text(encoding="utf-8")
    family = _STATE["font"]
    chars = set(html.unescape("".join(re.findall(r">([^<]+)<", text)))) - set("\r\n\t")
    # which (italic, bold) faces the text uses: matplotlib writes separate
    # font-style / font-weight properties in each style="..." attribute
    variants = set()
    for m in re.finditer(r'style="([^"]*font-family[^"]*)"', text):
        style = m.group(1).lower()
        fs = re.search(r"font-style:\s*(\w+)", style)
        fw = re.search(r"font-weight:\s*(\w+)", style)
        variants.add((bool(fs) and fs.group(1) in ("italic", "oblique"),
                      bool(fw) and fw.group(1) in ("bold", "600", "700", "800", "900")))
    variants = variants or {(False, True)}
    faces = []
    for italic, bold in sorted(variants):
        prop = font_manager.FontProperties(family=family, weight="bold" if bold else "normal",
                                           style="italic" if italic else "normal")
        src = font_manager.findfont(prop, fallback_to_default=False)
        opts = subset.Options()
        opts.notdef_outline = True
        if src.lower().endswith(".ttc"):
            opts.font_number = 0
        ttf = subset.load_font(src, opts)
        sub = subset.Subsetter(opts)
        sub.populate(text="".join(sorted(chars)))
        sub.subset(ttf)
        buf = io.BytesIO()
        ttf.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        faces.append(f"@font-face{{font-family:'{family}';font-style:{'italic' if italic else 'normal'};"
                     f"font-weight:{'bold' if bold else 'normal'};"
                     f"src:url(data:font/ttf;base64,{b64}) format('truetype');}}")
    start = re.search(r"<svg\b[^>]*>", text)
    if not start:
        return "NOTE svg: could not find the <svg> tag; fonts not embedded"
    block = '<defs><style type="text/css">' + "".join(faces) + "</style></defs>"
    path.write_text(text[:start.end()] + block + text[start.end():], encoding="utf-8")
    return f"PASS svg: {len(faces)} font face(s) embedded as a subset ({len(chars)} characters)"


def save_modes(draw, name: str, folder: str | Path = ".",
               modes: tuple[str, ...] = MODES) -> dict[str, list[str]]:
    """Draw and save one figure in every colour mode, tidily:

        <folder>/output/normal/<name>_normal.png|_transparent.png|.pdf|.svg|.tif|_checks.txt
        <folder>/output/soft/<name>_soft....

    draw() builds and returns a NEW figure (ps.new_figure inside it, colours from a
    ColorRegistry created inside it); it is called once per mode, after apply(mode).
    Returns {mode: checks}. The style is set back to "normal" afterwards."""
    modes = tuple(modes)
    if not modes or any(m not in MODES for m in modes) or len(set(modes)) != len(modes):
        raise ValueError(f"modes must be a non-empty selection of {MODES}, got {modes!r}")
    results = {}
    try:
        for mode in modes:
            apply(mode=mode)
            fig = draw()
            if not isinstance(fig, mpl.figure.Figure):
                raise TypeError("draw() must return the figure it built (return fig)")
            results[mode] = save(fig, f"{name}_{mode}", Path(folder) / "output" / mode)
    finally:
        apply(mode="normal")
    return results


def save(fig, name: str, outdir: str | Path = ".") -> list[str]:
    """Save name.png (white, 600 dpi), name_transparent.png, name.pdf, name.svg
    (font subset embedded), name.tif (white, 1200 dpi, RGB, LZW) and name_checks.txt.
    Prints the checks; returns them."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    refresh_placements(fig)
    checks = check_figure(fig)
    fig.savefig(outdir / f"{name}.png", dpi=600)
    fig.savefig(outdir / f"{name}_transparent.png", dpi=600, transparent=True)
    fig.savefig(outdir / f"{name}.pdf")
    fig.savefig(outdir / f"{name}.svg")
    try:
        checks.append(_embed_svg_fonts(outdir / f"{name}.svg"))
    except Exception as exc:                      # embedding must never lose the figure
        checks.append(f"NOTE svg: fonts not embedded ({type(exc).__name__}: {exc})")
    _save_tiff(fig, outdir / f"{name}.tif")
    (outdir / f"{name}_checks.txt").write_text("\n".join(checks) + "\n", encoding="utf-8")
    plt.close(fig)
    print(f"[{name}]")
    for line in checks:
        print("  " + line)
    if any(c.startswith("FAIL") for c in checks):
        print("  -> fix every FAIL before showing this figure to the user")
    return checks

"""Diagrams for the `plotting` skill: flowcharts, calculation workflows, machine-learning and
computer-science architectures. Drawn in Typst with the fletcher package and the skill's
diagram style (stormy.typ), so they match the plots: Arial bold, 7 pt text in boxes, 6 pt
notes, 1 pt lines, the Lancet colours, normal and soft modes.

One copy lives in each project next to pubstyle.py (<figure root>/_style/pubdiagram.py, with
stormy.typ beside it); init_figure.py keeps both in step with the skill. The plot.py that
`init_figure.py <project> <name> --diagram` makes is just

    import pubdiagram as pd
    pd.render(HERE, WIDTH, MODES)        # compiles diagram.typ of this folder

Output, like every other figure (pubstyle 0.10.0 layout):
    output/<name>_<mode>.png (600 dpi) and .pdf (vector, text kept as text), output/checks.txt;
    `python plot.py --submit` adds .svg, a 1200-dpi .tif and _transparent.png.
A diagram without FAIL is copied to <figure root>/_preview/.

Checks (measured on the compiled PDF, not on the source):
    font     every embedded font is Arial (Typst math $...$ and characters Arial lacks
             pull in other fonts and FAIL)
    size     text sizes: none below 5 pt (sub/superscripts), none above 7 pt
    width    the diagram fits the chosen width (single 8.3 cm, onehalf 12 cm, double 17.4 cm)
             at 100 %, so the 7 pt text stays 7 pt in print
    typst    every compiler warning is a FAIL

Needs the Python package `typst` (pip install typst). The first compile downloads fletcher
from packages.typst.org into Typst's package cache; after that no network is needed.
"""
from __future__ import annotations

import io
import json
import re
import sys
import zlib
from pathlib import Path

import pubstyle as ps

DIAGRAM_VERSION = "0.1.0"
FLETCHER = "0.5.8"           # pinned in stormy.typ; 0.6 changed the shape API

# widest diagram allowed for each journal layout, cm (printed at 100 %)
WIDTH_CM = {"single": 8.3, "onehalf": 12.0, "double": 17.4}
MIN_PT, MAX_PT = 5.0, ps.LABEL_PT + 0.05
SOURCE = "diagram.typ"


def _typst():
    try:
        import typst
    except ImportError:
        raise SystemExit("Diagrams need the Python package typst: pip install typst "
                         "(or run with uv: uv run plot.py). Nothing was drawn.") from None
    return typst


def _font_dirs(font: str) -> list[str]:
    """Folders of the font files matplotlib found, so Typst sees the same Arial even when
    it sits in a user font folder."""
    from matplotlib import font_manager as fm
    return sorted({str(Path(f.fname).parent) for f in fm.fontManager.ttflist if f.name == font})


def _pdf_streams(data: bytes):
    yield data
    for m in re.finditer(rb"stream\r?\n", data):
        end = data.find(b"endstream", m.end())
        try:
            yield zlib.decompress(data[m.end():end])
        except zlib.error:
            continue


def measure_pdf(path: str | Path) -> dict:
    """Fonts, text sizes and page size of a PDF written by Typst."""
    data = Path(path).read_bytes()
    fonts, sizes = set(), set()
    for chunk in _pdf_streams(data):
        for name in re.findall(rb"/BaseFont\s*/(?:[A-Z]{6}\+)?([^\s/<>\[\]()]+)", chunk):
            fonts.add(re.sub(r"-Identity-[HV]$", "", name.decode("latin-1")))
        sizes.update(float(x) for x in re.findall(rb"(?<![\w.])(\d+(?:\.\d+)?) Tf", chunk))
    box = re.search(rb"/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]", data)
    w = h = float("nan")
    if box:
        x0, y0, x1, y1 = map(float, box.groups())
        w, h = (x1 - x0) / 72 * 2.54, (y1 - y0) / 72 * 2.54
    return {"fonts": sorted(fonts), "sizes": sorted(sizes), "width_cm": w, "height_cm": h}


def _font_ok(embedded: str, font: str) -> bool:
    squash = lambda s: re.sub(r"[\s_-]", "", s).lower()  # noqa: E731
    return squash(embedded).startswith(squash(font))


def check_diagram(pdf: Path, warnings, font: str, standin: bool, width: str) -> list[str]:
    m = measure_pdf(pdf)
    out = [f"NOTE style: pubdiagram {DIAGRAM_VERSION} (fletcher {FLETCHER}), colour mode {ps._STATE['mode']}"]
    if standin:
        out.append(f"NOTE font: {font} used as a DRAFT stand-in for Arial; redraw on a machine with Arial")
    other = [f for f in m["fonts"] if not _font_ok(f, font)]
    if other:
        out.append("FAIL font: not everything is in " + font + ": " + ", ".join(other) +
                   ". Typst math ($...$) and characters missing from Arial pull in other fonts; write "
                   "variables as #v[E], indices with #sub[...] / #super[...], Greek letters as characters")
    elif not m["fonts"]:
        out.append("NOTE font: no text found in the diagram")
    else:
        out.append(f"PASS font: every text is set in {font}")
    small = [s for s in m["sizes"] if s < MIN_PT - 0.01]
    big = [s for s in m["sizes"] if s > MAX_PT]
    if small or big:
        bits = ([f"below {MIN_PT:g} pt: " + ", ".join(f"{s:g}" for s in small)] if small else []) + \
               ([f"above {ps.LABEL_PT} pt: " + ", ".join(f"{s:g}" for s in big)] if big else [])
        out.append("FAIL text size: " + "; ".join(bits) + " (do not set text sizes in diagram.typ; "
                   "use #small[...] or note() for 6 pt)")
    else:
        out.append("PASS text size: " + ", ".join(f"{s:g}" for s in m["sizes"]) + " pt "
                   f"(boxes {ps.LABEL_PT} pt, notes 6 pt, indices ≥ {MIN_PT:g} pt)")
    limit = WIDTH_CM[width]
    size = f"{m['width_cm']:.1f} cm × {m['height_cm']:.1f} cm"
    if m["width_cm"] > limit + 0.05:
        shrink = limit / m["width_cm"]
        out.append(f"FAIL width: {size} is wider than '{width}' ({limit} cm); shrunk to fit, "
                   f"7 pt text would print at {7 * shrink:.1f} pt. Tighten spacing, break long "
                   "labels into two lines, or choose a wider layout")
    else:
        out.append(f"PASS width: {size}, fits '{width}' ({limit} cm) at 100 %")
    if m["height_cm"] > 23:
        out.append(f"NOTE height: {m['height_cm']:.1f} cm is taller than a journal page leaves room for")
    warns = [str(getattr(w, "message", w)) for w in warnings]
    out += [f"FAIL typst: {w}" for w in dict.fromkeys(warns)] or ["PASS typst: compiled without warnings"]
    return out


def _tiff(png: bytes, path: Path) -> None:
    from PIL import Image
    with Image.open(io.BytesIO(png)) as im:
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.convert("RGBA").split()[-1])
        bg.save(path, format="TIFF", compression="tiff_lzw", dpi=(ps.TIFF_DPI, ps.TIFF_DPI))


def render(folder: str | Path = ".", width: str = "double", modes=ps.MODES, formats=None,
           source: str = SOURCE, name: str | None = None) -> dict[str, list[str]]:
    """Compile <folder>/diagram.typ in every colour mode into <folder>/output/ and check it.
    width: 'single' (8.3 cm), 'onehalf' (12 cm) or 'double' (17.4 cm), the widest the
    diagram may be at print size. Returns {mode: checks}."""
    typst = _typst()
    folder = Path(folder).resolve()
    name = name or folder.name
    src = folder / source
    if not src.exists():
        raise SystemExit(f"{src} is missing; nothing was drawn.")
    if width not in WIDTH_CM:
        raise ValueError(f"width must be one of {tuple(WIDTH_CM)}, got {width!r}")
    modes = tuple(modes)
    if not modes or any(m not in ps.MODES for m in modes) or len(set(modes)) != len(modes):
        raise ValueError(f"modes must be a non-empty selection of {ps.MODES}, got {modes!r}")
    formats = ps._formats(formats)
    out = ps.prepare_output(folder, name)
    font, standin = ps._pick_font()
    common = dict(root=str(folder.parent), font_paths=_font_dirs(font))
    results = {}
    try:
        for mode in modes:
            ps.apply(mode=mode)
            inputs = {"mode": mode, "font": font,
                      "palette": json.dumps([ps.tone(c) for c in ps.CATEGORICAL])}
            stem = out / f"{name}_{mode}"
            try:
                pdf, warnings = typst.compile_with_warnings(str(src), format="pdf", sys_inputs=inputs, **common)
            except typst.TypstError as exc:
                raise SystemExit(f"Typst could not compile {src.name}:\n{exc}") from None
            stem.with_suffix(".pdf").write_bytes(pdf)
            checks = check_diagram(stem.with_suffix(".pdf"), warnings, font, standin, width)
            if "pdf" not in formats:
                stem.with_suffix(".pdf").unlink()
            if "png" in formats:
                typst.compile(str(src), output=str(stem.with_suffix(".png")), format="png", ppi=600,
                              sys_inputs=inputs, **common)
            if "transparent" in formats:
                typst.compile(str(src), output=str(out / f"{name}_{mode}_transparent.png"), format="png",
                              ppi=600, sys_inputs={**inputs, "transparent": "1"}, **common)
            if "svg" in formats:
                typst.compile(str(src), output=str(stem.with_suffix(".svg")), format="svg",
                              sys_inputs=inputs, **common)
                checks.append("NOTE svg: Typst writes text as outlines (looks right everywhere, "
                              "not editable as text); edit text in the PDF")
            if "tif" in formats:
                png = typst.compile(str(src), format="png", ppi=ps.TIFF_DPI, sys_inputs=inputs, **common)
                _tiff(png, stem.with_suffix(".tif"))
            results[mode] = checks
            print(f"[{name}_{mode}]")
            for line in checks:
                print("  " + line)
    finally:
        ps.apply(mode="normal")
    ps.write_checks(out, results)
    failed = any(c.startswith("FAIL") for r in results.values() for c in r)
    if failed:
        print("  -> fix every FAIL before showing this diagram to the user")
    pngs = [out / f"{name}_{m}.png" for m in modes] if "png" in formats else []
    ps.publish_preview(folder, pngs, not failed)
    return results


if __name__ == "__main__":
    sys.exit(__doc__)

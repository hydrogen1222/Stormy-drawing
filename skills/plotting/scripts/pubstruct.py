#!/usr/bin/env python3
"""EXPERIMENTAL: draw one structure with every drawing package that is available, so the
user can look at the results side by side and pick the one that looks best.

Used by the plot.py that `init_figure.py <project> <name> --structure` creates; the project
gets its own copy next to pubstyle.py (figures/_style/pubstruct.py). Needs ase and numpy;
every other package is optional and is skipped, with the reason, when it is missing.

    import pubstruct as pst
    rows = pst.render_all("data/structure.cif", out_dir, "003_Li2S_cell_normal",
                          colors={"Li": "#00468B", "S": "#FDAF91"})

Every picture is written as  <name>_<package>.<ext>  (the package name is the suffix, so
pictures of the same structure never overwrite each other), plus <name>_packages.txt
that lists for each package: OK / SKIPPED (why) / FAILED (why), and its version.

Packages (tag = file suffix):
  raycast       own numpy ray-caster, orthographic, nothing to install       crystal, molecule
  ase           ase.io.write png (plain flat discs, the baseline)           crystal, molecule
  povray        ase + the POV-Ray program (ray-traced)                       crystal, molecule
  ovito         ovito Python module, Tachyon renderer (needs a Vulkan driver) crystal, molecule
  jmol          Jmol jar through java (set JMOL_JAR or put `jmol` on PATH)   crystal, molecule
  materia       Typst package @preview/materia (python package `typst`)     crystal, molecule
  rdkit         RDKit 2D skeletal formula (needs a SMILES or a mol file)     molecule
  typed-smiles  Typst package @preview/typed-smiles                          molecule
Tested here: raycast, ase, materia, rdkit, typed-smiles. povray, ovito and jmol could not be
run where this module was written (no program / no Vulkan driver); they are written from the
documentation and skip themselves when the program is missing. Fix them on first real use.
"""
from __future__ import annotations

import itertools
import math
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

STRUCT_VERSION = "0.1.0"

ALL_PACKAGES = ("raycast", "ase", "povray", "ovito", "jmol", "materia", "rdkit", "typed-smiles")
WIDTH_CM = 8.0            # same width as the standard canvas of pubstyle
DPI = 600
BOND_FACTOR = 1.15        # automatic bonds: different elements closer than factor x (r_cov + r_cov)
DEFAULT_RADIUS_SCALE = 0.40   # displayed radius = scale x covalent radius, unless RADII says otherwise
BOUNDARY_TOL = 0.02       # fractional distance to a cell face that counts as "on the face"


class Skip(Exception):
    """A package that cannot run here; the message says why."""


@dataclass
class Row:
    tag: str
    status: str                   # OK, SKIPPED or FAILED
    note: str = ""
    files: list = field(default_factory=list)
    version: str = ""


# ------------------------------------------------------------------ structure input

@dataclass
class Scene:
    atoms: object                 # ase.Atoms, cell + positions in the camera-independent frame
    periodic: bool
    colors: dict                  # element -> "#RRGGBB"
    radii: dict                   # element -> displayed radius, Å
    bonds: list                   # (i, j) index pairs into atoms
    rules: list                   # [(el_a, el_b, cutoff)], for packages that bond by rule
    view: tuple                   # (azimuth, elevation) degrees
    smiles: str | None
    molfile: str | None
    px: int = round(WIDTH_CM / 2.54 * DPI)
    note: str = ""


def _hex_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def view_basis(view):
    """Right, up and viewing direction (orthographic) for (azimuth, elevation) in degrees.
    Azimuth 0 looks along +y, positive azimuth turns the camera toward +x; elevation lifts
    the camera above the xy plane."""
    az, el = (math.radians(a) for a in view)
    cam = np.array([math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)])
    d = -cam
    right = _unit(np.cross(d, [0, 0, 1]))
    up = np.cross(right, d)
    return right, up, d


def read_structure(path: str | Path | None, smiles: str | None = None, molfile: str | None = None):
    """ase.Atoms from a structure file (CIF, POSCAR/CONTCAR, xyz, ...), or from a SMILES /
    mol file through RDKit (one 3D conformer, random but fixed seed). Returns (atoms, note)."""
    if path:
        from ase.io import read
        atoms = read(str(path))
        return atoms, ""
    from rdkit import Chem
    from rdkit.Chem import AllChem
    mol = Chem.MolFromMolFile(str(molfile), removeHs=False) if molfile else Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("RDKit could not read the SMILES / mol file")
    mol = Chem.AddHs(mol)
    if AllChem.EmbedMolecule(mol, randomSeed=7) != 0:
        raise ValueError("RDKit could not make a 3D conformer for this molecule")
    from ase import Atoms
    conf = mol.GetConformer()
    atoms = Atoms([a.GetSymbol() for a in mol.GetAtoms()],
                  positions=[list(conf.GetAtomPosition(i)) for i in range(mol.GetNumAtoms())])
    return atoms, "3D coordinates are an arbitrary RDKit conformer, not a computed structure"


def expand_boundary(atoms, tol: float = BOUNDARY_TOL):
    """Add the periodic images of atoms lying on a cell face, as VESTA does, so a corner atom
    appears at all eight corners. Atoms elsewhere are untouched."""
    from ase import Atoms
    frac = atoms.get_scaled_positions(wrap=True)
    sym = atoms.get_chemical_symbols()
    out_f, out_s = [], []
    for f, s in zip(frac, sym):
        axes = [[0.0, 1.0] if x < tol or x > 1 - tol else [x] for x in f]
        for combo in itertools.product(*axes):
            out_f.append(combo)
            out_s.append(s)
    return Atoms(out_s, scaled_positions=out_f, cell=atoms.cell, pbc=False)


def auto_bonds(atoms, rules, periodic: bool = False, factor: float = BOND_FACTOR):
    """Index pairs to draw as bonds. rules = {("Li", "S"): 2.6} gives the cutoff (Å) per
    element pair; rules=None bonds atoms closer than factor x (r_cov + r_cov). In a crystal
    only different elements are bonded automatically (so Li2S gets no Li-Li bonds); in a
    molecule every pair is (C-C needs it)."""
    from ase.data import atomic_numbers, covalent_radii
    pos, sym = atoms.get_positions(), atoms.get_chemical_symbols()
    cut = {}
    for (a, b), c in (rules or {}).items():
        cut[frozenset((a, b))] = c
    pairs = []
    for i, j in itertools.combinations(range(len(atoms)), 2):
        key = frozenset((sym[i], sym[j]))
        if rules is not None:
            c = cut.get(key)
        elif periodic and sym[i] == sym[j]:
            c = None
        else:
            c = factor * (covalent_radii[atomic_numbers[sym[i]]] + covalent_radii[atomic_numbers[sym[j]]])
        if c is not None and np.linalg.norm(pos[i] - pos[j]) < c:
            pairs.append((i, j))
    return pairs


def default_radii(elements, scale=DEFAULT_RADIUS_SCALE, overrides=None):
    from ase.data import atomic_numbers, covalent_radii
    out = {e: scale * float(covalent_radii[atomic_numbers[e]]) for e in elements}
    out.update(overrides or {})
    return out


def elements_of(path: str | Path | None, smiles: str | None = None, molfile: str | None = None):
    atoms, _ = read_structure(path, smiles, molfile)
    return sorted(set(atoms.get_chemical_symbols()), key=lambda e: atoms.get_chemical_symbols().index(e))


def make_scene(path, colors, *, smiles=None, molfile=None, radii=None, bonds=None,
               supercell=(1, 1, 1), view=(25.0, 15.0), px=None) -> Scene:
    atoms, note = read_structure(path, smiles, molfile)
    periodic = bool(atoms.pbc.any() and atoms.cell.volume > 1e-6)
    if periodic:
        if tuple(supercell) != (1, 1, 1):
            atoms = atoms.repeat(tuple(supercell))
        atoms = expand_boundary(atoms)
    else:
        atoms.set_pbc(False)
    elems = sorted(set(atoms.get_chemical_symbols()), key=atoms.get_chemical_symbols().index)
    missing = [e for e in elems if e not in colors]
    if missing:
        raise ValueError(f"no color for {missing}: pass colors={{element: '#RRGGBB'}} "
                         "(plot.py takes them from the color registry)")
    rules = [(a, b, c) for (a, b), c in bonds.items()] if bonds else []
    s = Scene(atoms=atoms, periodic=periodic, colors={e: colors[e] for e in elems},
              radii=default_radii(elems, overrides=radii), bonds=auto_bonds(atoms, bonds, periodic),
              rules=rules, view=tuple(view), smiles=smiles, molfile=molfile, note=note)
    if px:
        s.px = int(px)
    return s


def _camera_atoms(s: Scene):
    """Copy of the atoms (and cell) rotated into the camera frame: x right, y up, z to the viewer."""
    right, up, d = view_basis(s.view)
    R = np.array([right, up, -d])
    a = s.atoms.copy()
    a.positions = s.atoms.positions @ R.T
    a.cell = np.asarray(s.atoms.cell) @ R.T
    return a, R


def _extent(s: Scene):
    """Projected size of the picture in Å: (xmin, xmax, ymin, ymax), atoms with their radii."""
    a, _ = _camera_atoms(s)
    r = np.array([s.radii[e] for e in a.get_chemical_symbols()])
    p = a.positions[:, :2]
    return (p[:, 0] - r).min(), (p[:, 0] + r).max(), (p[:, 1] - r).min(), (p[:, 1] + r).max()


def _version(mod: str) -> str:
    try:
        from importlib.metadata import version
        return version(mod)
    except Exception:
        return ""


# ------------------------------------------------------------------ raycast (own, numpy)

BOND_R, EDGE_R, EDGE_COLOR = 0.13, 0.035, (0.30, 0.30, 0.34)


def _r_raycast(s: Scene, stem: Path):
    a, R = _camera_atoms(s)
    pos, sym = a.positions, a.get_chemical_symbols()
    prims = []
    for p, e in zip(pos, sym):
        prims.append(("s", p, s.radii[e], np.array(_hex_rgb(s.colors[e]))))
    for i, j in s.bonds:
        m = 0.5 * (pos[i] + pos[j])
        prims.append(("c", pos[i], m, BOND_R, np.array(_hex_rgb(s.colors[sym[i]]))))
        prims.append(("c", pos[j], m, BOND_R, np.array(_hex_rgb(s.colors[sym[j]]))))
    if s.periodic:
        c = np.asarray(a.cell)
        corner = {k: sum(k[i] * c[i] for i in range(3)) for k in itertools.product([0, 1], repeat=3)}
        for k1, k2 in itertools.combinations(corner, 2):
            if sum(abs(x - y) for x, y in zip(k1, k2)) == 1:
                prims.append(("c", corner[k1], corner[k2], EDGE_R, np.array(EDGE_COLOR)))

    ss = 2
    x0, x1, y0, y1 = _extent(s)
    if s.periodic:                        # the cell frame belongs to the picture too
        cc = np.array([sum(k[i] * np.asarray(a.cell)[i] for i in range(3)) for k in itertools.product([0, 1], repeat=3)])
        x0, x1 = min(x0, cc[:, 0].min()), max(x1, cc[:, 0].max())
        y0, y1 = min(y0, cc[:, 1].min()), max(y1, cc[:, 1].max())
    pad = 0.04 * max(x1 - x0, y1 - y0)
    x0, x1, y0, y1 = x0 - pad, x1 + pad, y0 - pad, y1 + pad
    w_px, h_px = s.px, max(2, round(s.px * (y1 - y0) / (x1 - x0)))
    W, H = w_px * ss, h_px * ss
    scale = W / (x1 - x0)                 # pixels per Å
    ox, oy = x0, y1

    depth = np.full((H, W), np.inf, np.float32)
    normal = np.zeros((H, W, 3), np.float32)
    color = np.ones((H, W, 3), np.float32)
    hit = np.zeros((H, W), bool)
    ex, ey, ez = np.array([1.0, 0, 0]), np.array([0, 1.0, 0]), np.array([0, 0, 1.0])
    d = -ez                               # the camera frame looks along -z

    def px_of(p):
        return (p[0] - ox) * scale, (oy - p[1]) * scale

    for pr in prims:
        if pr[0] == "s":
            _, c, r, col = pr
            cx, cy = px_of(c)
            rp = r * scale
            bb = (cx - rp, cx + rp, cy - rp, cy + rp)
        else:
            _, p0, p1, r, col = pr
            (ax_, ay_), (bx_, by_) = px_of(p0), px_of(p1)
            rp = r * scale
            bb = (min(ax_, bx_) - rp, max(ax_, bx_) + rp, min(ay_, by_) - rp, max(ay_, by_) + rp)
        xa, xb = max(int(bb[0]) - 1, 0), min(int(bb[1]) + 2, W)
        ya, yb = max(int(bb[2]) - 1, 0), min(int(bb[3]) + 2, H)
        if xb <= xa or yb <= ya:
            continue
        xs, ys = np.meshgrid(np.arange(xa, xb) + 0.5, np.arange(ya, yb) + 0.5)
        u, v = xs / scale + ox, oy - ys / scale
        O = np.stack([u, v, np.full_like(u, 50.0)], -1)       # ray origins in front of the scene
        if pr[0] == "s":
            oc = O - c
            b = oc @ d
            disc = b * b - (np.sum(oc * oc, -1) - r * r)
            ok = disc > 0
            t = -b - np.sqrt(np.where(ok, disc, 0))
            P = O + t[..., None] * d
            n = (P - c) / r
        else:
            axis = p1 - p0
            L = np.linalg.norm(axis)
            ax = axis / L
            dd = d - (d @ ax) * ax
            A2 = dd @ dd
            if A2 < 1e-9:
                continue
            oo = (O - p0) - ((O - p0) @ ax)[..., None] * ax
            B2 = 2 * (oo @ dd)
            C2 = np.sum(oo * oo, -1) - r * r
            disc = B2 * B2 - 4 * A2 * C2
            ok = disc > 0
            t = (-B2 - np.sqrt(np.where(ok, disc, 0))) / (2 * A2)
            P = O + t[..., None] * d
            sp = (P - p0) @ ax
            ok &= (sp >= 0) & (sp <= L)
            n = P - p0 - sp[..., None] * ax
            n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-12
        sl = (slice(ya, yb), slice(xa, xb))
        better = ok & (t < depth[sl])
        depth[sl] = np.where(better, t, depth[sl])
        normal[sl][better] = n[better]
        color[sl][better] = col
        hit[sl] |= better

    key = _unit(ez + 0.9 * ey - 0.7 * ex)
    fill = _unit(ez - 0.5 * ey + 0.8 * ex)
    nd, nf = np.clip(normal @ key, 0, 1), np.clip(normal @ fill, 0, 1)
    spec = np.clip(normal @ _unit(key + ez), 0, 1) ** 60
    img = color * (0.38 + 0.62 * nd + 0.18 * nf)[..., None] + 0.28 * spec[..., None]
    if hit.any():                         # distant atoms fade slightly toward white
        t_n = np.where(hit, (depth - depth[hit].min()) / (np.ptp(depth[hit]) + 1e-9), 0)[..., None]
        img = img * (1 - 0.14 * t_n) + 0.14 * t_n
    img = np.where(hit[..., None], np.clip(img, 0, 1), 1.0)
    img = img.reshape(h_px, ss, w_px, ss, 3).mean(axis=(1, 3))
    from matplotlib.image import imsave
    out = stem.with_name(stem.name + "_raycast.png")
    imsave(out, img)
    return [out], "numpy"


# ------------------------------------------------------------------ ase / povray

def _ase_lists(s: Scene, a):
    sym = a.get_chemical_symbols()
    return [s.radii[e] for e in sym], [_hex_rgb(s.colors[e]) for e in sym]


def _r_ase(s: Scene, stem: Path):
    from ase.io import write
    a, _ = _camera_atoms(s)
    radii, cols = _ase_lists(s, a)
    x0, x1, y0, y1 = _extent(s)
    scale = s.px / ((x1 - x0) * 1.08)
    out = stem.with_name(stem.name + "_ase.png")
    write(str(out), a, format="png", rotation="", radii=radii, colors=cols,
          show_unit_cell=2 if s.periodic else 0, scale=scale, maxwidth=s.px + 50)
    return [out], _version("ase")


def _r_povray(s: Scene, stem: Path):
    if shutil.which("povray") is None:
        raise Skip("the povray program is not installed (ase only writes the scene for it)")
    from ase.io.pov import write_pov
    a, _ = _camera_atoms(s)
    radii, cols = _ase_lists(s, a)
    out = stem.with_name(stem.name + "_povray.png")
    with tempfile.TemporaryDirectory() as tmp:
        pov = write_pov(Path(tmp) / "scene.pov", a, radii=radii, colors=cols, rotation="",
                        povray_settings=dict(canvas_width=s.px, celllinewidth=0.04,
                                             bondatoms=s.bonds, transparent=False,
                                             display=False, pause=False, camera_type="orthographic"))
        pov.render()
        shutil.copy(Path(tmp) / "scene.png", out)
    return [out], "povray"


# ------------------------------------------------------------------ ovito

def _ovito_worker(p: dict) -> None:
    """Runs in a child process (ovito can abort the whole process when its headless Qt
    platform cannot start, which no try/except catches)."""
    from ovito.io import import_file
    from ovito.modifiers import CreateBondsModifier
    from ovito.vis import Viewport, TachyonRenderer
    pipeline = import_file(p["file"])
    types = pipeline.source.data.particles_.particle_types_
    for e, hexc in p["colors"].items():
        t = types.type_by_name_(e)
        t.radius, t.color = p["radii"][e], _hex_rgb(hexc)
    mod = CreateBondsModifier(mode=CreateBondsModifier.Mode.Pairwise)
    for a_, b_, c_ in p["rules"]:
        mod.set_pairwise_cutoff(a_, b_, c_)
    mod.vis.width, mod.vis.use_particle_colors = 2 * BOND_R, True
    pipeline.modifiers.append(mod)
    if p["periodic"]:
        pipeline.source.data.cell_.vis.line_width = 2 * EDGE_R
    pipeline.add_to_scene()
    w, h = p["size"]
    vp = Viewport(type=Viewport.Type.Ortho, camera_dir=tuple(p["dir"]))
    vp.zoom_all((w, h))
    vp.render_image(size=(w, h), filename=p["out"], background=(1, 1, 1),
                    renderer=TachyonRenderer(ambient_occlusion=True, shadows=False))


def _r_ovito(s: Scene, stem: Path):
    import importlib.util
    import json
    if importlib.util.find_spec("ovito") is None:
        raise Skip("python package ovito is not installed")
    from ase.io import write
    right, up, d = view_basis(s.view)
    x0, x1, y0, y1 = _extent(s)
    size = [s.px, max(2, round(s.px * (y1 - y0) / (x1 - x0)))]
    out = stem.with_name(stem.name + "_ovito.png")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        write(str(tmp / "scene.extxyz"), s.atoms, format="extxyz")
        (tmp / "p.json").write_text(json.dumps(dict(
            file=str(tmp / "scene.extxyz"), out=str(out), size=size, dir=[float(x) for x in d],
            colors=s.colors, radii=s.radii, rules=[list(r) for r in s.rules], periodic=s.periodic)))
        env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
        r = subprocess.run([sys.executable, "-I", str(Path(__file__).resolve()), "--ovito-worker",
                            str(tmp / "p.json")], env=env, capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or not out.exists():
        err = (r.stderr or "").strip()
        if "Vulkan" in err:
            raise Skip("ovito needs a Vulkan driver (e.g. mesa-vulkan-drivers); none found")
        if "Qt platform plugin" in err:
            raise Skip("ovito cannot start its headless Qt platform here")
        raise RuntimeError(err.splitlines()[-1] if err else f"ovito exited with code {r.returncode}")
    return [out], _version("ovito")


# ------------------------------------------------------------------ jmol

def _jmol_command():
    jar = os.environ.get("JMOL_JAR")
    if jar and Path(jar).exists() and shutil.which("java"):
        return ["java", "-jar", jar]
    exe = shutil.which("jmol") or shutil.which("jmol.sh")
    if exe:
        return [exe]
    raise Skip("Jmol not found: put `jmol` on PATH or set JMOL_JAR to Jmol.jar (needs java)")


def _r_jmol(s: Scene, stem: Path):
    cmd = _jmol_command()
    from ase.io import write
    x0, x1, y0, y1 = _extent(s)
    w_px, h_px = s.px, max(2, round(s.px * (y1 - y0) / (x1 - x0)))
    out = stem.with_name(stem.name + "_jmol.png")
    az, el = s.view
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        src = tmp / ("scene.cif" if s.periodic else "scene.xyz")      # a CIF carries the cell
        write(str(src), s.atoms, format="cif" if s.periodic else "xyz")
        lines = [f'load "{src.as_posix()}"', "background white", "set antialiasDisplay true",
                 "wireframe 0.14", "set perspectiveDepth false"]
        for e, hexc in s.colors.items():
            rgb = " ".join(str(int(round(c * 255))) for c in _hex_rgb(hexc))
            lines.append(f"select {e}; color {{{rgb}}}; spacefill {s.radii[e]:.3f}")
        lines.append("select all")
        if s.periodic:
            lines.append("unitcell on")
        # the rotation is an approximation of the (azimuth, elevation) of the other packages
        lines += [f"reset; rotate x {-(90 - el):.2f}; rotate z {-az:.2f}",
                  f'write IMAGE {w_px} {h_px} PNG 2 "{out.as_posix()}"', "exitJmol"]
        (tmp / "draw.spt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        subprocess.run(cmd + ["-n", "-g", f"{w_px}x{h_px}", "-s", str(tmp / "draw.spt")],
                       check=True, capture_output=True, timeout=300)
    if not out.exists():
        raise RuntimeError("Jmol ran but wrote no image")
    return [out], "jmol"


# ------------------------------------------------------------------ typst packages

def _typst():
    try:
        import typst
    except ImportError:
        raise Skip("python package typst is not installed (pip install typst)") from None
    return typst


def _fmt(x):
    return f"{float(x):.6f}"


def _typ_color_dict(s: Scene):
    return "(" + ", ".join(f'"{e}": rgb("{c}")' for e, c in s.colors.items()) + ",)"


def _compile_typ(src: str, stem: Path, tag: str, vector=("svg", "pdf")):
    typst = _typst()
    files = []
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "fig.typ"
        f.write_text(src, encoding="utf-8")
        out = stem.with_name(f"{stem.name}_{tag}.png")
        typst.compile(str(f), output=str(out), format="png", ppi=DPI)
        files.append(out)
        for fmt in vector:
            o = stem.with_name(f"{stem.name}_{tag}.{fmt}")
            typst.compile(str(f), output=str(o), format=fmt)
            files.append(o)
    return files


def _r_materia(s: Scene, stem: Path):
    typst = _typst()
    a = s.atoms
    sym = a.get_chemical_symbols()
    width = f"{WIDTH_CM}cm"
    azel = f"(azimuth: {s.view[0]}deg, elevation: {s.view[1]}deg)"
    colors = _typ_color_dict(s)
    if s.periodic:
        frac = a.get_scaled_positions(wrap=False)
        keep = []                            # materia adds the boundary images itself
        seen = set()
        for i, f in enumerate(np.mod(np.round(frac, 5), 1.0)):
            key = (sym[i],) + tuple(np.round(f, 4))
            if key not in seen:
                seen.add(key)
                keep.append(i)
        cell = np.asarray(a.cell)
        lat = "(" + ", ".join("(" + ", ".join(_fmt(x) for x in v) + ")" for v in cell) + ")"
        atoms = "(" + ", ".join(f'("{sym[i]}", ({", ".join(_fmt(x) for x in np.mod(np.round(frac[i], 5), 1.0))}))'
                                for i in keep) + ",)"
        rules = ("(" + ", ".join(f'(elements: ("{x}", "{y}"), max: {c})' for x, y, c in s.rules) + ",)") if s.rules else "auto"
        body = (f"#let st = structure(lattice: {lat}, atoms: {atoms})\n"
                f"#crystal(st, view: {azel}, bonds: {rules}, colors: {colors}, legend: false, axes: false, width: {width})\n")
        imp = "structure, crystal"
    else:
        atoms = "(" + ", ".join(f'("{e}", ({", ".join(_fmt(x) for x in p)}))'
                                for e, p in zip(sym, a.positions)) + ",)"
        pairs = "(" + ", ".join(f"({i}, {j})" for i, j in s.bonds) + ",)" if s.bonds else "none"
        body = (f"#let st = structure(atoms: {atoms}, bonds: {pairs})\n"
                f"#molecule(st, view: {azel}, colors: {colors}, legend: false, width: {width})\n")
        imp = "structure, molecule"
    src = (f'#import "@preview/materia:0.1.0": {imp}\n#set page(width: auto, height: auto, margin: 4pt)\n' + body)
    return _compile_typ(src, stem, "materia"), "materia 0.1.0, typst " + _version("typst")


def _smiles_of(s: Scene) -> str:
    if s.periodic:
        raise Skip("a periodic crystal has no SMILES / skeletal formula")
    if s.smiles:
        return s.smiles
    if s.molfile:
        from rdkit import Chem
        return Chem.MolToSmiles(Chem.MolFromMolFile(s.molfile))
    raise Skip("give SMILES (or a mol file) for skeletal formulas; coordinates alone do not fix bond orders")


def _r_typed_smiles(s: Scene, stem: Path):
    smi = _smiles_of(s)
    src = ('#import "@preview/typed-smiles:0.13.0": smiles\n'
           "#set page(width: auto, height: auto, margin: 4pt)\n"
           f'#context {{ let c = smiles("{smi}"); scale(8cm / measure(c).width * 100%, c, reflow: true) }}\n')
    return _compile_typ(src, stem, "typed-smiles"), "typed-smiles 0.13.0, typst " + _version("typst")


# ------------------------------------------------------------------ rdkit

def _r_rdkit(s: Scene, stem: Path):
    smi = _smiles_of(s)
    try:
        from rdkit import Chem
        from rdkit.Chem.Draw import rdMolDraw2D
    except ImportError:
        raise Skip("python package rdkit is not installed") from None
    mol = Chem.MolFromMolFile(s.molfile) if s.molfile and not s.smiles else Chem.MolFromSmiles(smi)
    from rdkit.Chem import rdDepictor
    rdDepictor.Compute2DCoords(mol)
    xy = mol.GetConformer().GetPositions()[:, :2]
    span = xy.max(0) - xy.min(0)
    k = s.px / (span[0] + 3.0)                       # pixels per bond-length unit: width = the 8 cm canvas
    w, h = s.px, max(60, int(round(k * (span[1] + 3.0))))
    files = []
    for fmt, make in (("png", rdMolDraw2D.MolDraw2DCairo), ("svg", rdMolDraw2D.MolDraw2DSVG)):
        d = make(w, h)
        d.drawOptions().bondLineWidth = max(2, round(k / 25))
        d.DrawMolecule(mol)
        d.FinishDrawing()
        out = stem.with_name(f"{stem.name}_rdkit.{fmt}")
        if fmt == "png":
            out.write_bytes(d.GetDrawingText())
        else:
            out.write_text(d.GetDrawingText(), encoding="utf-8")
        files.append(out)
    return files, "rdkit " + _version("rdkit")


RENDERERS = {"raycast": _r_raycast, "ase": _r_ase, "povray": _r_povray, "ovito": _r_ovito,
             "jmol": _r_jmol, "materia": _r_materia, "rdkit": _r_rdkit, "typed-smiles": _r_typed_smiles}


# ------------------------------------------------------------------ driver

def render_all(path, out_dir, name, colors, *, smiles=None, molfile=None, radii=None, bonds=None,
               supercell=(1, 1, 1), view=(25.0, 15.0), packages=None, px=None) -> list[Row]:
    """Draw the structure with every package in `packages` (default: all) that can run.

    path        structure file (CIF, POSCAR/CONTCAR, xyz, ...) or None when smiles/molfile is given
    out_dir     output folder, e.g. <figure folder>/output/normal
    name        file stem, e.g. "003_Li2S_cell_normal"; the package name is appended
    colors      {element: "#RRGGBB"} from the project's color registry (reg.color(el))
    bonds       {("Li", "S"): 2.6} cutoffs in Å per element pair; None = automatic
    Returns one Row per package and writes <name>_packages.txt next to the pictures."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / name
    s = make_scene(path, colors, smiles=smiles, molfile=molfile, radii=radii, bonds=bonds,
                   supercell=supercell, view=view, px=px)
    kind = "crystal" if s.periodic else "molecule"
    rows = []
    for tag in (packages or ALL_PACKAGES):
        if tag not in RENDERERS:
            raise ValueError(f"unknown package {tag!r}; choose from {ALL_PACKAGES}")
        try:
            files, ver = RENDERERS[tag](s, stem)
            rows.append(Row(tag, "OK", files=[f.name for f in files], version=ver))
        except Skip as e:
            rows.append(Row(tag, "SKIPPED", str(e)))
        except Exception as e:                       # one failing package must not stop the others
            rows.append(Row(tag, "FAILED", f"{type(e).__name__}: {str(e)[:300]}"))
    lines = [f"pubstruct {STRUCT_VERSION}  (EXPERIMENTAL)  {kind}, {len(s.atoms)} atoms drawn, "
             f"view azimuth/elevation {s.view[0]}/{s.view[1]} deg"]
    if s.note:
        lines.append("NOTE " + s.note)
    for r in rows:
        extra = f"  [{r.version}]" if r.version else ""
        lines.append(f"{r.status:8s} {r.tag:13s} {', '.join(r.files) if r.files else r.note}{extra}")
    (out_dir / f"{name}_packages.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[{name}]")
    for ln in lines:
        print("  " + ln)
    return rows


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--ovito-worker":
        import json
        _ovito_worker(json.loads(Path(sys.argv[2]).read_text()))
    else:
        sys.exit(__doc__)

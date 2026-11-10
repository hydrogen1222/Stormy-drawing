#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["matplotlib>=3.8", "numpy", "ase"]
# ///
"""__FIGURE_NAME__

EXPERIMENTAL structure figure: draws one crystal or molecule with every drawing package that
is installed, so the user can compare the pictures and choose. Run in this folder:
    uv run plot.py     (or: python plot.py)
Every picture is output/<mode>/<folder>_<mode>_<package>.png (materia, typed-smiles, rdkit also
.svg; typst ones also .pdf); <folder>_<mode>_packages.txt says which packages ran, which were
skipped and why. Package list and what each one needs: figures/_style/pubstruct.py (top).
Structure file or SMILES, source and settings: README.md.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "_style"))   # figures/_style/pubstyle.py and pubstruct.py
import pubstyle as ps  # noqa: E402
import pubstruct as pst  # noqa: E402

# ---- settings (these are the only lines that ever need editing)
STRUCTURE_FILE = "structure.cif"  # in data/: CONTCAR, POSCAR, CIF, xyz ...; None if SMILES / MOLFILE is used
SMILES = None          # molecule: skeletal formulas (rdkit, typed-smiles) need it; without a structure
                       # file the 3D pictures use an arbitrary RDKit conformer (the report says so)
MOLFILE = None         # or a .mol/.sdf file name in data/
VIEW = (25.0, 15.0)    # (azimuth, elevation) in degrees; orthographic, about the same in every package
SUPERCELL = (1, 1, 1)  # crystals only
BONDS = None           # {("Li", "S"): 2.6} cutoff in Å per element pair; None = automatic (see pubstruct.py)
RADII = {}             # displayed radius in Å per element, e.g. {"Li": 0.42, "S": 0.66}; default 0.4 x covalent
PACKAGES = None        # None = every package; once the user has chosen, e.g. ("materia",)
MODES = ("normal", "soft")   # once the user has chosen, keep only that one (see README.md)

path = HERE / "data" / STRUCTURE_FILE if STRUCTURE_FILE else None
if path is not None and not path.exists():
    sys.exit(f"data/{STRUCTURE_FILE} is missing: copy the structure file into this folder's data/ "
             "(or set STRUCTURE_FILE = None and give SMILES).")
molfile = str(HERE / "data" / MOLFILE) if MOLFILE else None
if path is None and not (SMILES or molfile):
    sys.exit("give STRUCTURE_FILE, SMILES or MOLFILE at the top of plot.py.")

elements = pst.elements_of(path, SMILES, molfile)
try:
    for mode in MODES:
        ps.apply(mode=mode)                       # sets the colour mode that reg.color() uses
        reg = ps.ColorRegistry()                  # element colours are the project's fixed ones
        colors = {el: reg.color(el) for el in elements}
        pst.render_all(path, HERE / "output" / mode, f"{HERE.name}_{mode}", colors,
                       smiles=SMILES, molfile=molfile, radii=RADII, bonds=BONDS,
                       supercell=SUPERCELL, view=VIEW, packages=PACKAGES)
finally:
    ps.apply(mode="normal")

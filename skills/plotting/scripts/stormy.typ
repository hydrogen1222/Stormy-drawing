// stormy.typ - diagram style of the Stormy-drawing `plotting` skill (flowcharts, workflows,
// ML / CS architectures). Drawn with the Typst package fletcher; see references/diagrams.md.
//
// A project keeps its own copy at <figure root>/_style/stormy.typ (init_figure.py copies it
// and keeps it in step with the skill). A figure's diagram.typ starts with
//
//     #import "../_style/stormy.typ": *
//     #show: setup
//     #canvas( step((0, 0), [DFT], name: <dft>), flow(<dft>, <ml>), ... )
//
// plot.py (pubdiagram.py) compiles it with the project's font and colour mode. The file also
// compiles on its own (Tinymist live preview in VS Code, typst watch): then the defaults
// below are used (Arial, normal colours).
//
// Do not edit the copy in a project; change the skill and run init_figure.py --update-style.

#import "@preview/fletcher:0.5.8" as fletcher: diagram, node, edge
#let shapes = fletcher.shapes

#let STORMY-DIAGRAM = "0.1.0"

// ---------------------------------------------------------------- inputs from pubdiagram.py
#let _in = sys.inputs
#let mode = _in.at("mode", default: "normal")
#let font = _in.at("font", default: "Arial")
#let transparent = _in.at("transparent", default: "0") == "1"
// Lancet six colours (navy, red, green, purple, teal, peach), softened in soft mode by Python
#let palette = if "palette" in _in {
  json(bytes(_in.palette)).map(rgb)
} else {
  ("#00468B", "#ED0000", "#42B540", "#925E9F", "#0099B4", "#FDAF91").map(rgb)
}

// ---------------------------------------------------------------- sizes (same as the plots)
#let label-pt = 7pt      // text in boxes (= axis titles of the plots)
#let note-pt = 6pt       // edge labels, notes, group titles (= tick numbers, legends)
#let line-pt = 1pt       // every line: boxes, arrows, panels
#let ink = luma(20%)     // strokes and arrows without a colour (text itself is black)
#let paper = if transparent { none } else { white }

// ---------------------------------------------------------------- colours
// tone: 0-5 picks a palette colour, none = neutral grey. Fill is a light tint of it, the
// outline the colour itself (pale colours such as the peach are darkened for the outline).
#let _pick(tone) = palette.at(calc.rem(tone, palette.len()))
#let tone-color(tone) = if tone == none { ink } else {
  let c = _pick(tone)
  if oklab(c).components().at(0) > 75% { c.darken(35%) } else { c }
}
#let tone-fill(tone, strength: 1) = if tone == none { luma(96%) } else {
  _pick(tone).lighten(if mode == "soft" { 100% - 10% * strength } else { 100% - 14% * strength })
}

// ---------------------------------------------------------------- page and text
#let setup(body) = {
  set page(width: auto, height: auto, margin: 1.5pt, fill: paper)
  set text(font: font, size: label-pt, weight: "bold", fill: black)
  set par(leading: 0.45em)
  set sub(size: 5pt)      // indices 5 pt everywhere (Nature's minimum), also in 6 pt notes
  set super(size: 5pt)
  body
}

// variables in italic, like the plots: #v[E], #v[h]#sub[#v[i]]. Greek letters and
// operators are typed as characters (ε σ ∑ ∂ ∇ → ×); Typst math ($...$) is not used,
// its letters are not Arial (the check fails on it).
#let v(x) = text(style: "italic", x)
// a second, smaller line inside a box: [Train #small[MACE fine-tune]]
#let small(x) = { linebreak(); text(size: note-pt, x) }

// ---------------------------------------------------------------- the diagram
#let canvas(..args) = diagram(
  spacing: (9mm, 6mm),
  node-stroke: line-pt + ink,
  node-fill: luma(96%),
  node-corner-radius: 2.5pt,
  node-inset: 5pt,
  edge-stroke: line-pt + ink,
  mark-scale: 100%,
  label-size: note-pt,
  label-sep: 0.3em,
  crossing-fill: if transparent { white } else { paper },
  ..args,
)

// ---------------------------------------------------------------- boxes
// All take (position, content) and any fletcher node argument (name: <label>, width:, ...).

// a processing step: rounded rectangle
#let step(pos, body, tone: none, ..args) = node(pos, align(center, body), shape: shapes.rect,
  fill: tone-fill(tone), stroke: line-pt + tone-color(tone), ..args)

// the thing being trained or the central model: stronger tint
#let model(pos, body, tone: 0, ..args) = node(pos, align(center, body), shape: shapes.rect,
  fill: tone-fill(tone, strength: 2.2), stroke: line-pt + tone-color(tone), ..args)

// data, input or output: parallelogram
#let data(pos, body, tone: none, ..args) = node(pos, align(center, body),
  shape: shapes.parallelogram.with(angle: 15deg), fill: tone-fill(tone),
  stroke: line-pt + tone-color(tone), ..args)

// a stored set (database, training set): cylinder
#let store(pos, body, tone: none, ..args) = node(pos, align(center, body),
  shape: shapes.cylinder, fill: tone-fill(tone), stroke: line-pt + tone-color(tone), ..args)

// a yes/no question: diamond
#let decide(pos, body, tone: none, ..args) = node(pos, align(center, body),
  shape: shapes.diamond, fill: tone-fill(tone), stroke: line-pt + tone-color(tone), ..args)

// start or end: pill
#let terminal(pos, body, tone: none, ..args) = node(pos, align(center, body),
  shape: shapes.pill, fill: tone-fill(tone), stroke: line-pt + tone-color(tone), ..args)

// an operation inside a network (+, ×, σ, concat): small circle
#let op(pos, body, ..args) = node(pos, body, shape: shapes.circle, inset: 2.5pt,
  fill: white, stroke: line-pt + ink, ..args)

// free text without a box (6 pt), e.g. a remark beside an arrow
#let note(pos, body, ..args) = node(pos, text(size: note-pt, body), stroke: none,
  fill: none, ..args)

// a dashed panel around boxes that belong together, with a title (6 pt) at `at`:
//   ..group(<a>, <b>, title: [Interaction block × #v[T]], at: (1, -0.7), tone: 3)
// The spread `..` is needed: group gives two nodes (the title and the panel).
#let group(..args) = {
  let members = args.pos()
  let named = args.named()
  let title = named.remove("title", default: none)
  let at = named.remove("at", default: none)
  let tone = named.remove("tone", default: none)
  let out = ()
  if title != none and at != none {
    out.push(node(at, text(size: note-pt, title), stroke: none, fill: none))
    members.push(at)
  }
  let c = tone-color(tone)
  out.push(node(enclose: members, inset: 6pt, corner-radius: 4pt,
    fill: if tone == none { luma(97.5%) } else { _pick(tone).lighten(95%) },
    stroke: (paint: c.lighten(25%), thickness: line-pt, dash: (2.5pt, 1.8pt)), ..named))
  out
}

// ---------------------------------------------------------------- arrows
// main flow: solid arrow (stealth head, as in TikZ)
#let flow(..args) = edge(..args, "-stealth")
// optional or feedback path: dashed arrow
#let aside(..args) = edge(..args, "-stealth", dash: (3pt, 2pt))
// association without direction: plain line
#let connect(..args) = edge(..args, "-")

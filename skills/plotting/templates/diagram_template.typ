// __FIGURE_NAME__ : the drawing. plot.py compiles it; style and helpers: ../_style/stormy.typ
// Helpers: step  model  data  store  decide  terminal  op  note  group   |  flow  aside  connect
// Positions are (column, row) on a grid; name every box (name: <x>) and draw arrows between names.
// Text: #v[E] italic variable, #sub[i] / #super[2] indices, #small[...] second line at 6 pt.
#import "../_style/stormy.typ": *
#show: setup

#canvas(
  data((0, 0), [Input], name: <in>),
  step((1, 0), [Process], name: <proc>),
  decide((2, 0), [Good?], name: <ok>),
  terminal((3, 0), [Result], tone: 2, name: <out>),

  flow(<in>, <proc>),
  flow(<proc>, <ok>),
  flow(<ok>, <out>, label: [yes]),
  aside(<ok>, <proc>, bend: 50deg, label: [no]),
)

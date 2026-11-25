// Example: a classic computer-science flowchart, training a model with early stopping.
#import "../_style/stormy.typ": *
#show: setup

#canvas(
  spacing: (8mm, 7mm),
  terminal((0, 0), [Start], name: <start>),
  step((0, 1), [Train one epoch #small[mini-batches, Adam]], tone: 0, name: <train>),
  step((0, 2), [Validate #small[loss #v[L]#sub[val]]], name: <val>),
  decide((0, 3), [#v[L]#sub[val] improved?], name: <imp>),
  step((1, 3), [Save checkpoint #small[patience = 0]], tone: 2, name: <save>),
  step((-1, 3), [patience + 1], tone: 1, name: <wait>),
  decide((0, 4), [patience ≥ #v[P] ?], name: <stop>),
  terminal((0, 5), [Load best checkpoint], tone: 2, name: <end>),

  flow(<start>, <train>),
  flow(<train>, <val>),
  flow(<val>, <imp>),
  flow(<imp>, <save>, label: [yes]),
  flow(<imp>, <wait>, label: [no], label-side: right),
  connect(<wait>, (-1, 3.45), (0, 3.45)),
  flow(<save>, (1, 3.45), (0, 3.45), <stop>),
  flow(<stop>, <end>, label: [yes], label-side: left),
  aside(<stop>, (-1.7, 4), (-1.7, 1), <train>, label: [no], label-pos: 10%, label-side: right),
)

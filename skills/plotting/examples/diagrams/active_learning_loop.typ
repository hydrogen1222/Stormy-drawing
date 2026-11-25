// Example: active-learning loop for a machine-learning interatomic potential (MLIP).
// A generic workflow for illustration, not a record of any real project.
#import "../_style/stormy.typ": *
#show: setup

#canvas(
  spacing: (8mm, 9mm),
  store((0, 0), [Training set #small[DFT energies, forces]], tone: 4, name: <set>),
  model((1, 0), [Train MLIP #small[committee of 4]], tone: 0, name: <train>),
  step((2, 0), [MD with MLIP #small[NVT, 600–1000 K]], name: <md>),
  decide((3, 0), [max #v[σ]#sub[#v[F]] > #v[δ] ?], name: <unc>),
  step((3, 1), [Select new #small[uncertain frames]], name: <pick>),
  step((0, 1), [DFT single points #small[VASP, same settings]], tone: 1, name: <dft>),
  terminal((4, 0), [Production MD], tone: 2, name: <prod>),

  flow(<set>, <train>),
  flow(<train>, <md>),
  flow(<md>, <unc>),
  flow(<unc>, <pick>, label: [yes], label-side: left),
  flow(<pick>, <dft>),
  flow(<dft>, <set>),
  flow(<unc>, <prod>, label: [no]),
  ..group(<set>, <train>, <md>, <unc>, <pick>, <dft>, title: [Active-learning loop],
          at: (1.5, 0.5), tone: 4),
)

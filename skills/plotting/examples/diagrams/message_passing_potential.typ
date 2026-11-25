// Example: architecture of a message-passing interatomic potential (generic, MACE/NequIP-like).
#import "../_style/stormy.typ": *
#show: setup

#canvas(
  spacing: (7mm, 5mm),
  data((0, 0), [Structure #small[{#v[Z]#sub[#v[i]], #v[r]#sub[#v[i]]}]], name: <in>),
  step((0, 1), [Neighbour graph #small[#v[r]#sub[#v[ij]] < #v[r]#sub[cut]]], name: <graph>),
  step((0, 2), [Embedding #small[#v[h]#sub[#v[i]]#super[(0)] from #v[Z]#sub[#v[i]]]], name: <emb>),
  step((0, 3), [Message #small[#v[m]#sub[#v[ij]] = #v[φ]\(#v[h]#sub[#v[j]], #v[r]#sub[#v[ij]]\)]], tone: 3, name: <msg>),
  op((0, 4), [∑], name: <agg>),
  step((0, 5), [Update #small[#v[h]#sub[#v[i]]#super[(#v[t]+1)]]], tone: 3, name: <upd>),
  step((0, 6), [Readout #small[site energy #v[ε]#sub[#v[i]]]], name: <read>),
  op((0, 7), [∑], name: <sum>),
  terminal((0, 8), [Energy #v[E]], tone: 0, name: <E>),
  terminal((1, 8), [Forces #small[#v[F]#sub[#v[i]] = −∂#v[E] / ∂#v[r]#sub[#v[i]]]], tone: 1, name: <F>),

  flow(<in>, <graph>),
  flow(<graph>, <emb>),
  flow(<emb>, <msg>),
  flow(<msg>, <agg>, label: [over #v[j]], label-side: left),
  flow(<agg>, <upd>),
  aside(<upd>, <msg>, bend: -70deg, label: [#v[t] < #v[T]]),
  flow(<upd>, <read>),
  flow(<read>, <sum>, label: [over #v[i]], label-side: left),
  flow(<sum>, <E>),
  aside(<E>, <F>, label: [autograd]),
  ..group(<msg>, <agg>, <upd>, title: [Interaction × #v[T]], at: (1, 3), tone: 3),
)

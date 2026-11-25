# 流程图和示意图（`--diagram`）

计算流程、机器学习的训练/主动学习循环、网络结构、算法流程图这类"框 + 箭头"的图。用 Typst 的 fletcher 包画，样式文件 `figures/_style/stormy.typ` 把它和其他图统一起来：Arial 全加粗，框里 7 磅、注释 6 磅、上下标 5 磅，所有线 1 磅，Lancet 六色，normal 和 soft 两份。

不归这里管的：晶体、分子结构图（`references/structures.md`）；数据曲线（`figure-types.md`）；拼图用的色标条、图例（`pubparts.py`）。

## 开一张图

```bash
python <skill>/scripts/init_figure.py <项目根目录> MLIP_active_learning_loop --diagram
```

得到 `figures/NNN_MLIP_active_learning_loop/`，顶层是 `README.md`、`plot.py`、`diagram.typ`、`archive/`，第一次运行后多一个 `output/`。示意图没有数据，所以没有 `data/`，图本身就是 `diagram.typ`。

1. 在 `diagram.typ` 里画（下面的函数）。
2. `plot.py` 里设宽度 `WIDTH`：`"single"`（8.3 cm，单栏）、`"onehalf"`（12 cm）、`"double"`（17.4 cm，双栏）。这是按原大印刷时允许的最大宽度，超了检查报 FAIL，不靠缩小来塞进去（缩小会让 7 磅字变小）。
3. 运行 `python plot.py`。和其他图一样输出到 `output/`，没有 FAIL 的复制进 `figures/_preview/`。
4. 亲眼看图（见下面"看图时查什么"），报告时给出 `_preview/` 里那张 PNG 的路径。

第一次编译会从 packages.typst.org 下载 fletcher（之后在本机缓存里，不再联网）。需要 Python 包 `typst`（`pip install typst`；用 `uv run plot.py` 会自动装）。

边改边看：VS Code 装 Tinymist 插件，打开 `diagram.typ` 就有实时预览（这时用默认的 Arial 和 normal 配色）。

## 函数（都在 `stormy.typ` 里）

位置是网格坐标 `(列, 行)`，可以写小数。每个框给一个名字 `name: <x>`，箭头按名字连。

| 函数 | 画成 | 用于 |
|---|---|---|
| `step(pos, [...])` | 圆角矩形 | 一步处理（DFT 计算、训练一轮、写文件） |
| `model(pos, [...], tone: 0)` | 圆角矩形，底色更深 | 图的主角：被训练的模型、核心算法 |
| `data(pos, [...])` | 平行四边形 | 输入、输出、数据 |
| `store(pos, [...])` | 圆柱 | 数据集、数据库、训练集 |
| `decide(pos, [...])` | 菱形 | 是/否判断 |
| `terminal(pos, [...])` | 胶囊 | 开始、结束、最终结果 |
| `op(pos, [∑])` | 小圆 | 网络里的运算：∑、×、+、拼接 |
| `note(pos, [...])` | 只有 6 磅字 | 旁注 |
| `..group(<a>, <b>, title: [...], at: (x, y))` | 虚线圆角底板 | 把一组框圈起来，`at` 是标题的位置（标题也被圈进去）。前面的 `..` 不能少 |
| `flow(<a>, <b>)` | 实线箭头 | 主流程 |
| `aside(<a>, <b>)` | 虚线箭头 | 回路、可选步骤、反馈 |
| `connect(<a>, <b>)` | 无箭头的线 | 关联、汇合 |

- 颜色：`tone: 0`–`5` 依次是藏青、红、绿、紫、青、桃色（底色是该色的浅色，边框是该色）；不写是中性灰。颜色要有意义：同一类步骤同一种颜色（例如 DFT 都用红、机器学习都用藏青），一张图里有颜色的框不超过三四种，其余用灰。
- 箭头参数直接用 fletcher 的：`label: [yes]`、`label-side: left`、`bend: 40deg`、`corner: right`（直角折线），中间加折点：`flow(<a>, (2, 1.5), (0, 1.5), <b>)`。
- 框里第二行小字：`[Train MLIP #small[committee of 4]]`。
- 其他 fletcher 写法（`node`、`edge`、`shapes`）都能直接用，说明见 https://typst.app/universe/package/fletcher 。

## 公式和符号的写法

图里所有字都必须是 Arial（检查量的是 PDF 里实际嵌入的字体）。Typst 的公式模式 `$...$` 里的字母不是 Arial，**不要用**，改用：

| 要写的 | 写法 |
|---|---|
| 斜体变量 *E* | `#v[E]` |
| 下标 *h*ᵢ、上标 | `#v[h]#sub[#v[i]]`、`#super[(0)]`、`#v[r]#sub[cut]`（下标是文字时正体） |
| 希腊字母、运算符 | 直接打字符：`ε σ δ φ ∑ ∂ − × ≥ ≤ →`（`−` 是减号 U+2212，不是连字符） |
| 函数 *φ*(*x*) | `#v[φ]\(#v[x]\)`：紧跟在 `#v[...]` 后面的 `(` 和 `[` 要写成 `\(` `\[`，否则 Typst 当成函数调用 |

Arial 里没有的字符（例如 ∇）会从别的字体借，检查会报 FAIL 并列出字体名；换一种写法（"grad"、"autograd"）或用文字说明。

## 已定的样式（`stormy.typ`，和曲线图一致）

- 字号：框里 7 磅（= 坐标轴标题），箭头标签、注释、组标题 6 磅（= 刻度数字），上下标 5 磅（Nature 的最小值）。`diagram.typ` 里不许另设字号和字体。
- 线：框、箭头、虚线底板都是 1 磅，深灰；字一律黑色。箭头头是 stealth 形（细长，和 TikZ 一样）。
- 不加图标题；(a)(b) 由用户在图像编辑软件里加。
- normal 和 soft 两份，用户选一种；同一篇论文的图（曲线和示意图）用同一种。

## 自动检查（`output/checks.txt`）

量的是编译出来的 PDF，不是看源文件：

- `font`：嵌入的字体全是 Arial。用了 `$...$` 或 Arial 没有的字符就 FAIL。
- `text size`：所有字在 5–7 磅之间。
- `width`：按原大印刷不超过 `WIDTH`；超了会写出缩小后字会变成几磅。修法：缩小间距（`canvas(spacing: (7mm, 5mm), ...)`）、长标签拆两行、换成竖排，或者确实需要时把 `WIDTH` 换宽一档。
- `typst`：编译器的每条警告都是 FAIL。

## 看图时查什么

- 一眼能看出 README 里那句"想说明什么"吗？阅读顺序是否从左到右或从上到下，回路是否一眼看得出是回路？
- 箭头有没有穿过框、和别的线重叠、箭头头挤在一起？
- 标签（yes/no）是否紧挨着它说的那根线？
- 颜色是否表示类别，而不是每个框随便一种颜色？

## 例子

`examples/diagrams/` 里有三张（内容是通用示意，不是任何真实计算）：

- `active_learning_loop.typ`：机器学习势的主动学习循环（圆柱、菱形、组、回路），双栏宽。
- `message_passing_potential.typ`：消息传递势函数的网络结构（竖排、∑ 运算、带 × *T* 的组、下标），单栏宽。
- `training_early_stopping.typ`：带早停的训练流程（经典流程图：判断、汇合、左侧回路），1.5 栏宽。

`python examples/demo_diagrams.py <输出目录>` 把它们全部画一遍。

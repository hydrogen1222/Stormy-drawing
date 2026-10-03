---
name: plotting
description: Make publication-quality figures for Stormy's computational projects with matplotlib (DOS, band structures, NEB barriers, RDF, MSD, Arrhenius plots, 2D maps, bar charts) and structure figures, each in its own reproducible figure folder with data, script and recipe. Use for any figure, plot or chart, including redrawing a rejected one.
---

# 绘图（plotting）

这个 skill 规定 Stormy 课题里的图怎么画、放在哪、怎么保证以后能重画。任何画图、改图、重画的任务都先读这一页。

本 skill 可以单独使用，也可以和 AI-Computational-Chemist 装在同一个项目里。两者同时存在时，那边的画图规则（`knowledge/scientific-visualization.md`、`report` skill 的 figure 规则）与本 skill 冲突的地方，**以本 skill 为准**。例如那里默认 7 磅字、用脚本拼 (a)(b) 子图，这里是 10 磅字、只画单张图。

来源：https://github.com/hydrogen1222/Stormy-drawing ，作者 Stormy 与 Claude。

## 什么时候读哪个文件

| 情况 | 打开 |
|---|---|
| 第一次在某台机器上画图（装 Arial、准备 Python 环境） | `references/setup.md` |
| 开始画一张新图 | 本页"画一张新图的步骤"，再用 `scripts/init_figure.py` |
| 画态密度、能带、能垒、径向分布函数、均方位移、阿伦尼乌斯图、二维色图、柱状图 | `references/figure-types.md` 里对应的那一节 |
| 画晶体结构图 | `references/structures.md` |
| 想看每种图在假数据上的样子，或者测试样式模块 | `examples/demo_all_types.py` |
| 改样式本身（字号、颜色、刻度） | 不要自己改，先问 Stormy；改动写进本页"已定的样式" |

## 目录结构

图放在项目根目录下的 `figures/`，和计算目录并列。每张图一个文件夹：

```
figures/
  _style/
    pubstyle.py        本项目的样式模块（所有 plot.py 都调用它）
    colors.json        颜色登记文件（元素、原子对、结构等的固定颜色）
  001_Li6PS5Cl_bulk_DOS/
    dos_elements.dat   数据：从计算目录复制来的，不是链接
    plot.py            画图脚本，在这个文件夹里运行就能重画
    README.md          配方说明（模板见 templates/README_template.md）
    001_Li6PS5Cl_bulk_DOS.png               白底，600 DPI
    001_Li6PS5Cl_bulk_DOS_transparent.png   透明底，600 DPI
    001_Li6PS5Cl_bulk_DOS.pdf / .svg        矢量图，文字可编辑
    001_Li6PS5Cl_bulk_DOS_checks.txt        自动检查结果
    archive/           被替换掉的旧版本
```

- 文件夹名：三位编号 + 尽量详细的英文单词，不用中文、不用字母代号。编号和计算目录的编号无关。
- 数据一律**复制**进图的文件夹，不用软链接，`plot.py` 不许去读计算目录里的文件。
- `_style/` 每个项目一份，从本 skill 的 `scripts/pubstyle.py` 复制而来。改了它，本项目所有图下次重画时一起变；别的项目不受影响。

## 画一张新图的步骤

1. 想清楚这张图要说明什么，一句话。说不出来就先别画。
2. 运行 `python <skill>/scripts/init_figure.py <项目根目录> <英文描述名>`，得到新的图文件夹。
3. 从计算目录提取数据（vaspkit、nebresults.pl、自己的分析脚本），把结果文件复制进图文件夹。
4. 先填 `README.md`：数据从哪台机器哪个目录来、怎么提取的、每一列是什么和单位、哪列做横轴哪列做纵轴、能量零点等约定。
5. 照 `references/figure-types.md` 对应那一节改 `plot.py`，运行它。
6. 看终端里的检查结果，所有 FAIL 都要修掉。
7. **亲眼看一遍 PNG**（用能看图片的工具打开），按下面"出图后自查"逐条核对。
8. 把检查结果和你看图的结论写进 `README.md` 的"自查结果"。
9. 向 Stormy 报告时给出图文件夹的路径，一句话说这张图说明了什么。

## 重画一张被退回的图

1. 读这个文件夹的 `README.md` 和 `plot.py`，不要从头猜。
2. 把旧的 PNG、PDF、SVG 和 `plot.py` 移进 `archive/`，文件名加日期，例如 `plot_2026-10-03.py`。
3. 改 `plot.py`，重新运行，重新自查。
4. 在 `README.md` 的"修改记录"里写一行：改了什么、为什么（Stormy 的原话）、旧版本在哪。

## 已定的样式（2026-10-03 与 Stormy 商定，`pubstyle.py` 已实现）

字体和文字
- 只用 **Arial**。机器上没有 Arial 时脚本直接报错，不许换成别的字体（装法见 `references/setup.md`）。
- **全部加粗**：刻度数字、坐标轴标题、单位、图例、图中文字。
- 上下标、希腊字母、Å 等用 matplotlib 的公式写法渲染，例如 `r"cm$^{\rm 2}$"`、`r"$E-E_{\rm VBM}$"`。**不许**写成 `cm^2`，也**不许**用 ² ₁₀ 这类 Unicode 小字符，脚本会检查。
- 物理量符号斜体（*E*、*T*、*D*、*r*），单位和文字下标正体（`\rm`）。
- 坐标轴标题写成"物理量 (单位)"，单位放括号里。全部英文。
- 不加图标题，说明文字写在论文图注里。不画 (a)(b) 子图标签，Stormy 在 GIMP 里加。

坐标轴
- 闭合方框（四条边都画），**刻度朝外，主刻度和次刻度都有**，主刻度之间一个次刻度，和 Origin 一致。
- 只有一根横轴一根纵轴时，刻度只在左边和下边。唯一例外：阿伦尼乌斯图顶部的温度轴。
- 没有网格线。
- 轴的终点 = 数据最大值再加约 10%，向上取到下一个带数字的主刻度，每根轴 4–6 个数字（`ps.nice_limits`）。峰值 50 画到 60。
- 有自然零点的量（态密度、径向分布函数、计数、柱状图）从 0 开始。柱状图**必须**从 0 开始。
- 数据点不能压在图框上，需要时用 `pad_low` 在下面留空。
- 同一组对比图的坐标范围完全一致。
- 刻度数字小数位数统一（0.0、0.5、1.0）。不许出现轴角上的"×10⁻⁵"小字，数量级写进坐标轴标题。

画布和输出
- 三种画布：`standard` 8 cm × 6 cm（默认）、`tall` 6 cm × 8 cm（能带图）、`strip` 3 cm × 8 cm（能带图右边的态密度窄条）。10 磅字，在 GIMP 里一行拼三张时缩到约 7 磅，仍满足期刊要求。组会直接用同一张图。
- 同种画布的图框在画布里的位置固定，拼图时能对齐。带顶部第二横轴的图用 `ps.new_figure(top_axis=True)`，带色标条的图用 `ps.new_figure(colorbar=True)` 加 `ps.add_colorbar`，它们预留的空间也是固定的。刻度数字太长导致文字被裁掉时，检查会报 FAIL，先想办法缩短（换单位、改数量级），不要擅自改边距。
- 每张图输出：白底 PNG（600 DPI）、透明底 PNG、PDF、SVG。PDF/SVG 中文字可编辑。

线、点、图例
- 数据线 1.5 磅，图框 1.2 磅。离散数据点用空心圆（白色填充），平滑曲线只是连线，必须写明怎么来的。
- 参考线（能量零点、费米能级）用灰色细虚线（`ps.REFERENCE_LINE`）。
- 图例：小线段 + 黑字，无边框，默认右上角；用 `ps.place_legend`，它会自动避开数据（换角、分两列、或把纵轴提高一格）。只有一条曲线时不放图例。图例顺序和曲线在图上从上到下的顺序一致。

颜色
- 没有顺序的类别（元素、原子对、结构、方法）：柔和六色 `ps.CATEGORICAL`，已通过色盲检查。**通过颜色登记文件取色**：`reg.color("S")`（元素）、`reg.color("Li-S", "pair")`（原子对）、`reg.color("Br-doped", "structure")`（结构、路径）、`reg.color("Linear fit", "series")`（其他）。每组各有六色。第一次出现的键自动分配该组里一个没用过的颜色并写进 `colors.json`，以后永不改变。不预设元素种类，掺杂元素同样处理；S、Cl、P、Li 等常见元素空着时优先拿到习惯色（S 琥珀、Cl 青绿……）。结构图的原子颜色也读这个文件。
- 某组六色用完时不许造新颜色：改用线型或标记形状区分，或者拆图。
- 有顺序的量（温度、浓度、应变）：`ps.ordered_colors(n)`，暖色由浅到深，数值越大颜色越深。同一组图里有第二种有顺序的量时，第二种用 `ramp="cool"`。
- 有正负的量（差分电荷密度）：`ps.DIVERGING`，蓝—白—红，零点白色，色标范围对称。
- 文字一律黑色，不用曲线颜色写字。

## 出图后自查（agent 必须做）

`ps.save` 会自动检查并生成 `*_checks.txt`：字体、上下标写法、文字是否被裁掉、图例是否压住数据、轴角小字、图标题。全部 PASS 之后，还要**亲眼看图**核对：

- 这张图一眼能看出 README 里那句"想说明什么"吗？
- 坐标范围符合上面的规则吗？对比图之间一致吗？
- 曲线、标注、图例之间有没有重叠？数值标注的位数合理吗（能量一般两位小数）？
- 颜色是否来自登记文件、有顺序的量是否用了渐变？
- 有没有出现 matplotlib 默认样式（网格、彩虹色、DejaVu 字体）？
- 有 FAIL 或 NOTE 没处理的，不许交给 Stormy。用替身字体画的图（检查里 font 一行是 NOTE）只能当草稿，正式图必须在装了 Arial 的机器上重画。

## 禁止事项

- 不许编造或"美化"数据：不许手调数值、不许删点、不许在 README 没说明的情况下平滑或拟合。
- 不许把多个计算的图堆在同一个文件夹，也不许把图丢进一个大杂烩 `figures/` 根目录。
- 不许用软链接引用数据。
- 不许在 `plot.py` 里覆盖 `pubstyle.py` 的样式设置（字体、字号、刻度方向）。确实需要例外时先问 Stormy，并在 README 写明。

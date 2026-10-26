# 各类图的专门约定

> 画某一类图之前只读对应那一节。所有代码片段假设已经 `import pubstyle as ps`，画图部分写在 `plot.py` 的 `draw()` 里（`ps.save_modes` 会为 normal 和 soft 各调用一次，返回 `fig`；`reg = ps.ColorRegistry()` 也在 `draw()` 里取）。读数据和写 README 放在 `draw()` 外面，只做一次。
> 可运行的完整例子（假数据）在 `examples/demo_all_types.py`。

## 态密度（DOS / PDOS）

- **读数据和画图直接用 `pubstyle.py` 里的函数**，不要自己写（0.7.0 起）：
  ```python
  d = ps.read_dos(HERE / "data", formula_units=4)   # 读 data/ 里的 DOSCAR、POSCAR（或 CONTCAR）、EIGENVAL

  def draw():
      reg = ps.ColorRegistry()
      fig, ax = ps.new_figure()
      ps.plot_dos(ax, d, reg)                # 默认按元素；只画总态密度用 kind="total"
      ps.place_legend(ax)                    # 按轨道：kind={"S": ["p"], "P": ["s", "p"]}
      return fig

  ps.save_modes(draw, HERE.name, HERE)       # 写进 output/normal/ 和 output/soft/
  open(HERE / "README.md", "a").write(ps.dos_summary(d))   # 只在第一次画时追加，别重复追加
  ```
  把 `DOSCAR`、`POSCAR`、`EIGENVAL` 复制进图文件夹的 `data/`。缺 `EIGENVAL` 时 `read_dos` 会报错（没有它分不出绝缘体和金属，也没有带隙）；确知是金属时才用 `assume_metal=True`。`formula_units`（晶胞里有几个化学式单元）**必须自己给**，函数不猜；写进 README。零点：绝缘体取 EIGENVAL 里所有 k 点的价带顶，金属取 DOSCAR 里的费米能级。带隙取自 EIGENVAL，不取态密度边缘。占据带数取自 EIGENVAL 的占据数列，不是 NELECT/2（自旋轨道耦合时每条带只放一个电子，NELECT/2 会少算一半）；电子数为奇数而 ISPIN=1 时程序报错，不会当成绝缘体。元素/轨道曲线是投影到各原子周围球内的结果，加起来不等于总态密度，README 里写明。
- 按元素或按轨道画需要计算时设 `LORBIT = 11`（或 10）；DOSCAR 里没有分波态密度时只能画总的，`plot_dos` 会报错并提示。自旋极化（ISPIN=2）的态密度暂不支持，`read_dos` 会直接报错。
- 默认能量范围由 `ps.dos_energy_range` 按下面的规则算，`plot_dos(..., xlim=(lo, hi))` 可以覆盖，覆盖时在 README 里写理由。
- **能量零点**：绝缘体放在价带顶（VBM），从本征值里找（例如 vaspkit 输出的带边信息，或 EIGENVAL/vasprun.xml 中占据态的最高本征值），不用 OUTCAR 里的 E-fermi，因为绝缘体的费米能级在带隙里的位置是随意的。横轴写 `r"$E-E_{\rm VBM}$ (eV)"`。只有金属才用费米能级，写 `r"$E-E_{\rm F}$ (eV)"`。
- **默认按元素投影**，每种元素一条线；讨论成键时才按轨道（如 S 3p、P 3s）。元素颜色用 `reg.color("S")`；按轨道时用 `reg.color("S 3p", "series")` 这类键。
- **总态密度**用浅灰填充（`color="0.85"`），画在最底层。
- **纵轴归一化到每个化学式单元**，标题 `"DOS (states/eV/f.u.)"`。不同大小的超胞才能直接比。README 里写清除以了多少个化学式单元。
- **填色默认用渐变**（XPS 风格）：先 `ps.gradient_fill(ax, e, y, c)`，再 `ax.plot(e, y, color=c)` 把曲线画在上面。备选：半透明填色 `fill_between(alpha=0.3)`；堆叠填色（各元素逐层累加，顶线是总态密度，用来强调哪种元素主导某段能量）。
- **能量范围**不写死，按规则定：下限放在最靠近价带顶那一组价带的底部再往下一点，上限约为导带底以上 3 eV，两头取整数。README 写一句理由。
- **带隙**默认用双向箭头标出：`ps.gap_arrow(ax, 0.0, e_cbm, y=箭头高度)`，数值两位小数。
- **展宽**：只用 VASP 计算时的展宽（ISMEAR/SIGMA），画图时不额外平滑。确实要加，展宽宽度写进 README。
- **自旋极化**：自旋向上画正值、向下画负值，同一元素同一颜色，纵轴对称；README 注明"向下为负是画图约定"。
- 零点画参考虚线：`ax.axvline(0, **ps.REFERENCE_LINE)`。

## 能带

- 画布 `tall`（6 cm × 8 cm）。配态密度时，右边另画一张 `strip`（3 cm × 8 cm）的态密度窄条，**两张纵轴范围完全一致**，窄条不显示纵轴数字（`ax.tick_params(labelleft=False)`），横轴是态密度。之后在图像编辑软件里左右拼接。
- 零点同态密度（价带顶），纵轴 `r"$E-E_{\rm VBM}$ (eV)"`，零点画水平参考虚线。
- **读数据和画图直接用 `pubstyle.py` 里的函数**，不要自己写（0.6.0 起）：
  ```python
  b = ps.read_bands(HERE / "data")       # 读 data/ 里的 EIGENVAL、POSCAR（或 CONTCAR）、KPATH.in

  def draw():
      fig, ax = ps.new_figure("tall")
      ps.plot_bands(ax, b)               # 零点、竖线、标签、带边点、带隙标注都在里面
      return fig

  ps.save_modes(draw, HERE.name, HERE)
  open(HERE / "README.md", "a").write(ps.bands_summary(b))   # 数据来源、零点、带隙写进 README（只追加一次）
  ```
  把计算目录里的 `EIGENVAL`、`POSCAR`、`KPATH.in`（金属还要 `OUTCAR`）复制进图文件夹的 `data/` 即可。只读普通文本文件，有没有启用 HDF5 都一样，不需要 py4vasp。
- **两种 k 点写法都支持**：普通 PBE 能带（整条路径都有权重）；HSE06 的"SCF 网格 + 零权重路径点"（vaspkit 251）——有零权重点时只画零权重点，网格点不画，但价带顶按所有点（含网格）找。KPOINTS + KPOINTS_OPT 的写法（输出在 vasprun.xml 里）暂不支持。
- 路径中间的断开（如 U|K）自动识别，k 距离按真实倒格矢计算。读数据后先检查 `b.off_path`：为 True 说明带边在 SCF 网格上而不在画出的路径上，README 要写明。
- 自旋极化（ISPIN=2）的能带暂不支持，`read_bands` 会直接报错；真遇到再加（计划：向上实线、向下虚线）。
- **检查数据本身**：硅这类简并点（Γ 处价带顶三重简并）若三条带差 0.02 eV 以上，说明计算没收敛（EDIFF 太松或迭代太少），先告诉用户重算，不要照画。
- 高对称路径用 vaspkit 的 303 功能生成（按晶体对称性自动给路径），路径和 KPATH 文件来源写进 README。
- 高对称点处画灰色细竖线；横轴刻度标签用正确符号：`r"$\rm\Gamma$"`，不能写成 G；路径断开处标成 `"X|U"`。横轴不画次刻度，不写横轴标题。
- 普通能带全部用一种深色（`"0.15"`），线宽 1.0 磅（`ps.DATA_LW`）。价带顶和导带底各画一个小实心圆点（价带顶 `ps.CATEGORICAL[1]`、导带底 `ps.CATEGORICAL[0]`，`clip_on=False`；`ps.plot_bands` 已经这样画），之间用 `ps.gap_arrow(ax, 0.0, e_cbm, y=k位置, vertical=True, text_fmt="{:.2f} eV\n(direct)")` 标带隙，数值和 direct 分两行，免得文字横跨高对称点竖线（间接带隙写 indirect）。
- 带隙和直接/间接取自 EIGENVAL 里**所有** k 点（杂化泛函的 SCF 网格也算），不是只看画出来的路径：直接带隙 = 同一个 k 点同时有价带顶和导带底（简并、对称等价的点按能量相同处理，不按横轴位置比）。带边不在画出的路径上时，图上不画带隙标记和数值，README 里写全局带隙和路径上的带隙（`bands.gap`、`bands.gap_path`）。
- 金属的零点是 OUTCAR 里**最后一个** `E-fermi`；应取产生电荷密度的自洽（SCF）计算的 OUTCAR，非自洽能带计算的 E-fermi 可能有偏移，README 里写明用的是哪一个。
- 能量范围规则同态密度，能带图和窄条用同一个范围。
- 按元素着色的能带只在讨论成键时画。
- 计算方法（PBE 还是 HSE06，HSE06 能带用的是哪种做法）写进 README，图上不写。

## 迁移能垒（NEB）

- 数据来自 VTST 的 `nebresults.pl`（生成 `neb.dat`、`spline.dat`）或 vaspkit 的 NEB 后处理。
- **横轴默认用迁移距离**：`"Migration distance (Å)"`，取 neb.dat 里累计的距离列。备选"Reaction coordinate"（0 到 1，不同路径间无法比较长短）。Å 直接写在文字里即可，它不是上下标。
- 纵轴 `"Relative energy (eV)"`，起点结构能量设为 0。
- 每个中间结构画一个空心圆；连线用 `spline.dat` 的样条插值，不自己拟合。
- **能垒取中间结构里的最高能量**，不取插值曲线的最高点，标在最高点上方，两位小数，README 写明。
- 起点和终点能量不同（不对称路径）时，正向、逆向两个能垒都标出。
- **爬坡图像**：读这次计算的 INCAR，`ps.incar_true(path_to_INCAR_copy, "LCLIMB")`。为真时把最高的那个点画成实心圆；为假时全部空心，并在 README 写"未使用爬坡图像，能垒可能偏低"。（INCAR 同样要复制进图文件夹。）INCAR 里没写 `LCLIMB` 时，`incar_true` 会报错而不是猜：它的默认值随 VASP/VTST 版本而异，请在 INCAR 副本里明确写出；确实要假定时用 `default=True/False`，并把这个假定写进 README。同一行用分号写的多个标签（`ICHAIN = 0 ; LCLIMB = .TRUE.`）能正确识别。
- 纵轴用 `ps.nice_limits(ax, emax, headroom=0.25, pad_low=0.25)`：上面给数值标注留空，下面不让圆点压在图框上。
- 几条路径比较：放在同一张图，横轴统一用迁移距离，颜色 `reg.color("path A", "structure")` 这类。

## 径向分布函数（RDF）

- 横轴 `r"$r$ (Å)"`，**最远只画到晶胞最短边长的一半**，再往外受周期性边界影响失真。
- 纵轴 `r"$g(r)$"`，从 0 开始，远处应趋于 1；明显不趋于 1 时先查数据，不要直接画。
- 默认原子对 Li–S、Li–Cl、Li–Li（按体系实际情况），图例用短横线"–"连接元素，颜色 `reg.color("Li-S", "pair")`。
- README 写清：轨迹来源、丢掉的平衡段时长、用于平均的帧数、分格宽度。
- 配位数曲线 *n*(*r*) 不和 *g*(*r*) 共用一张图（那需要第二根纵轴），单独画。
- 不同温度对比时用 `ps.ordered_colors`。

## 均方位移（MSD）

- 横轴 `"Time (ps)"`，纵轴 `r"MSD (${\rm \AA}^{\rm 2}$)"`。默认画 Li；可加骨架元素（P、S、Cl 等）说明它们不动。
- 拟合扩散系数的时间区间用浅灰阴影标出（`ax.axvspan(t0, t1, color="0.9", zorder=0)`），扩散系数写在图中，例如 `r"$D$ = 1.2 × 10$^{\rm -6}$ cm$^{\rm 2}$ s$^{\rm -1}$"`。开头的非扩散段和末尾统计不足的一段不参与拟合，区间写进 README。
- 三维扩散 D = 斜率 / 6，README 写明公式和单位换算。
- 多个温度：`ps.ordered_colors(n)`，温度越高越深，图例从上到下按曲线从上到下排列（通常高温在上）。

## 阿伦尼乌斯图

- 横轴 `r"1000/$T$ (K$^{\rm {-}1}$)"`，纵轴 `r"log$_{\rm 10}$($D$/cm$^{\rm 2}$ s$^{\rm {-}1}$)"` 或电导率对应写法。负指数写成 `{-}1`，否则负号两边会多出空格。
- 用 `ps.new_figure(top_axis=True)` 预留顶部空间，再加温度轴（`ax.secondary_xaxis("top", functions=...)`），这是"刻度只在左下"规则的唯一例外；顶轴不画次刻度。
- 数据点空心圆，线性拟合用虚线；活化能和拟合误差标在图中（用 `ps.place_text`），例如 `r"$E_{\rm a}$ = 0.25 ± 0.02 eV"`。几个体系的活化能也可以写进图例，如 `"Crystal (0.29 eV)"`。
- 外推到室温的点用不同标记和虚线画出，README 注明是外推值，不是直接算的。

## 二维色图

- 有正负的量（差分电荷密度、电荷转移）：`cmap=ps.DIVERGING`，色标范围对称（`vmin=-a, vmax=a`），零点白色。
- 只有正值的量（锂离子概率密度、电荷密度）：`cmap=ps.sequential_cmap()`，零为白色。
- 范围固定、有物理分界的量（ELF 等，0 到 1）例外，用 `cmap="turbo"`，见下面 Multiwfn 平面图一条。
- **从分子动力学轨迹统计的密度图**（例如某一层里锂离子的概率密度）看起来"糊"、一格一格、满是噪点，原因不在图片分辨率，而在数据：分格太粗（0.25 Å 一格时，每个格子在图上就是一个看得见的小方块），每格里的计数又少（帧数少时低密度区全是零星噪点）。做法：
  1. 分格宽度 0.1 Å（`np.histogram2d`，范围取整个晶胞边长）。
  2. 用 `ps.smooth_density(H, sigma_bins=0.2 / 0.1)` 做高斯平滑，σ = 0.2 Å，周期性边界（默认 `periodic=True`）。平滑核归一化，原子总数不变。σ 不要超过 0.3 Å，否则相邻位点会糊在一起。
  3. 平滑之后再换算成密度：除以帧数、每格面积、层厚，单位 nm$^{-3}$。
  4. `ax.imshow(rho.T, origin="lower", extent=..., interpolation="bilinear")`。没平滑的原始计数不许用 bilinear 插值去"抹平"。
  5. 噪点还是多，就多用一些帧（加长轨迹或减小取样间隔），不要加大 σ。
  6. README 写清：层的位置和厚度、分格宽度、σ、用了多少帧、色标上限是否截断。
- 横纵轴都是 Å 时 `ax.set_aspect("equal")`，不许拉扁。这时画布可能留白，属正常。
- 用 `ps.new_figure(colorbar=True)` 建图，`ps.add_colorbar(fig, ax, im, label)` 加色标条（右侧，标题写物理量和单位）。对比的几张图色标范围完全一致。
- 切片平面上的原子用小圆点标出（颜色取自登记文件，黑色细描边）。
- README 写清：切片平面由哪几个原子或哪个晶面确定、插值方式、色标范围及是否截断。
- **Multiwfn 平面图（ELF、电子密度的切片）**：在 Multiwfn 主功能 4 里选函数、点数和由三个原子定义的平面，关掉图窗后在结果菜单里选 `Export the current plane data to plane.txt`（编号以屏幕为准），把文件复制进 `data/`。导出时屏幕会写 `length unit is in Angstrom`，文件有 6 列：前三列笛卡尔坐标 X Y Z，第 4、5 列是图上的 x、y，最后一列是数值。用 `m = ps.read_plane("data/plane.txt")` 读入：默认坐标是 Å（屏幕写的是 Bohr 就传 `unit="bohr"`），图的横纵轴 `m.u`、`m.v` 与 Multiwfn 的图一致，数值原样返回。
  - ELF 的范围固定为 0 到 1，色标用 Turbo：`im = ax.imshow(m.Z, origin="lower", extent=m.extent, cmap="turbo", vmin=0, vmax=1, interpolation="bilinear")`，色标标题写 `"ELF"`，同一组图（几处接触）色标必须同为 0–1。ELF 是解析光滑的场，可以用 bilinear；上面"不许"针对的是没平滑的原始计数。
  - 为什么这里不用白到深色的 `sequential_cmap()`：ELF 的 0.5（均匀电子气）是有物理意义的分界，文献也习惯用蓝到红的彩虹色读它；白底渐变会把 0.2–0.8 之间的区域糊成一片同色。Turbo 色相顺序是紫蓝、青绿、黄、橙红，近似 Multiwfn 默认的彩虹色（不是同一张色表），也是 VMD 的 Turbo 色标（`pubparts.colorbar` 的默认），和之后画的三维图配得上。`soft` 模式不改它，两种模式的色标一样。
  - Turbo 对红绿色盲不友好：README 写明色标，图里重要的结论靠位置和原子标注说明，不要只靠颜色。
  - 文件带三维坐标（6 列或 4 列）时，`u, v, h = m.project(xyz)` 把同一结构的原子坐标（Å）投到切片上，`h` 是离平面的距离。只标 `h` 小于约 0.5 Å 的原子（颜色取自登记文件）；离得更远的原子，价层被平面截到也会出现色块，但那不是平面上的原子，不画点。
  - 文件只有两列坐标（`x y 数值`）时 `m.project` 会报错，原子位置从 Multiwfn 带原子标注的图上读，写进 README。
  - 用赝势（如 CP2K 的 GTH）时，Li 的 1s² 作为价电子被显式保留，会出现 ELF≈1 的圆盘；O、S、Cl、P 的内层被赝势替掉，原子核处是低值小点，周围一圈是价层。README 注明，免得把 Li 圆盘当成键。
- 三维等值面属于结构图，见 `structures.md`。

## 沿某个方向的分布（界面剖面）

- 横轴是到界面的距离，例如 `r"$\zeta$ (Å)"`，界面处 `ax.axvline(0, **ps.REFERENCE_LINE)`；需要基准值（如比值 1）时同样画参考虚线。
- 一侧区域用浅灰背景 `ax.axvspan(x0, 0, color="0.93", zorder=0)`，区域名用 `ps.place_text(ax, "Crystal", x_range=(x0, 0))`，它会自己找空地，不压曲线（曲线挤在下面时加 `prefer="top"`）。
- 不确定度用同色浅色带 `fill_between(alpha=0.15)`，README 写明带宽代表什么（标准差、几次独立模拟）。
- 两个因素交叉（界面 × 方法）时用 `ps.factor_legend`，见 SKILL.md。

## 柱状图

- 纵轴**必须从 0 开始**。从中间开始会把小差别放大成大差别。
- 柱子之间留空隙，柱子用登记文件的颜色（`group="structure"`），可加 1.0 磅深色描边（`ps.FRAME_LW`）。
- 柱顶标数值时位数统一。
- 误差棒带短横帽，线宽 1.0 磅，README 写明误差棒代表标准差还是标准误差。

## 拼图用的矢量部件（`pubparts.py`）

用途：VMD、VESTA、OVITO 的位图是图的主体，周围的色标条、图例、比例尺等在这里画成矢量，再拖进 PS/AI 里拼。每个部件就是一张普通的图：新建一个图文件夹（如 `005_Turbo_colorbar_ESP`），`plot.py` 里 `import pubparts as pp`，`draw()` 返回部件，照常 `ps.save_modes(...)`。尺寸单位是 cm，存成多大放进 PS 就是多大。拼图时用 PDF 或 SVG，文字可编辑，背景透明。

```python
import pubparts as pp
def draw():
    return pp.colorbar(-0.05, 0.05, "ESP (a.u.)")     # 竖的 Turbo 色标条
```

| 部件 | 函数 | 要点 |
|---|---|---|
| 色标条 | `pp.colorbar(vmin, vmax, title, orientation, length_cm, thickness_cm, ticks, decimals, bands, reverse)` | 数值范围必须和 VMD 的 Color Scale Data Range 一致（第一个值对应最左端颜色，最后一个值对应最右端，中间线性）；`bands=n` 对应 VMD 的 posterize，`reverse=True` 对应反转。**不随柔和模式变色**，必须和位图保持一致。拼图前取 VMD 图里几个像素和色标条对一下 |
| 等值面图例 | `pp.isosurface_legend([0.002, -0.002], unit=..., title="Isovalue")` | 颜色默认正红负蓝（和 `ps.DIVERGING` 两端一致）；VMD 里用了别的颜色就把 `(值, 十六进制色)` 对传进去 |
| 元素图例 | `pp.element_legend(["Li", "P", "S", "Cl"])` | 颜色取自登记文件（和曲线图一致，随色调模式变）；要和 VMD 原子颜色一致时用 `colors={"Li": "#..."}`，给定的色号原样使用 |
| 坐标轴三角 | `pp.axes_triad(rotation, labels=("a", "b", "c"), vectors=晶格矢量)` | `rotation` 可直接给 VMD 的 `molinfo top get rotate_matrix`（4×4）；非正交晶胞传 `vectors`；朝向观察者的轴按投影画得很短 |
| 比例尺 | `pp.scale_bar(5, "Å", cm_per_unit)` | `cm_per_unit` = 图放进版面后 1 Å 有多少 cm（量一条已知长度，如晶胞边长，再相除）；条的长度就是这么长 |
| 区域条 | `pp.region_strip([("Crystal", 15), ("Glass", 15)], axis_label=..., boundary_extra_cm=0.4)` | 只看长度比例；虚线边界可延伸出去穿过相邻的图 |
| 能级图 | `pp.level_diagram(columns, links=...)` | 普通带框图，按常规检查；HOMO/LUMO、带边、缺陷态 |
| 放大小图框 | `pp.add_inset(ax, (x0, x1, y0, y1), (x, y, w, h))` | 加在任意普通图里，自动画虚线框和连线，返回小图的坐标轴，把同样的数据画进去 |
| 自由排版 | `pp.new_part(w_cm, h_cm)` 加 `pp.arrow / dashed_box / dashed_circle / dimension / label / line` | 箭头、虚线框、距离线（如 `2.45 Å`）、"Move up 0.6 Å"这类标注；坐标单位是 cm |

**画 VMD 静电势/轨道色标条的流程：**
1. 先向用户要三样：①Color Scale Data Range 的 min 和 max（VMD Tk Console 里 `mol scaleminmax top <repid>` 会返回，点过 Autoscale 的话就是数据的最小最大值）；②单位（a.u. 还是 kcal/mol 等）；③竖放还是横放。没有这两个数就不要猜，色标条数字错了从图上看不出来。
2. 默认是长而细的（长 6 cm、厚 0.22 cm），约 5 个整齐刻度，画布按内容裁掉空白。字号固定（刻度 6 pt、标题 7 pt），和其他图一致，不改。
3. 用户用一句话微调时，对应改这些参数：

| 用户说 | 改什么 |
|---|---|
| 更长/更短/更细/更粗 | `length_cm` / `thickness_cm` |
| 刻度和 VMD 自带的一样（11 个等分） | `ticks=11` |
| 刻度少一点/多一点 | `ticks=n`，或直接给列表 `ticks=[-40, -20, 0, 20, 40]` |
| 数字取整/多保留一位 | `decimals=0` / `decimals=2` |
| 横放 | `orientation="horizontal"` |
| 颜色分成几档（VMD 的 posterize） | `bands=n` |
| 颜色反过来 | `reverse=True` |
| 两端有超出范围的值 | `extend="both"`（或 `"min"` / `"max"`） |
| 改标题或单位 | 改 `title` |

刻度数字互相挤在一起时函数会报错并说明解决办法（少几个刻度、少几位小数、加长色标条），不会生成难看的图。字体的大小不能改：这是仓库的规则，需要缩放就在 PS 里整体缩放。

- 部件的检查：字体、字号、粗体、线宽（含方框、箭头的轮廓）和画布边缘照常检查；自由排版里文字压在线上是故意的，所以不查重叠。
- 所有线 1.0 磅、文字 6 pt（色标条标题 7 pt）、深灰 `0.15`，和其他图一致。
- 全部部件的示例：`examples/demo_parts.py`。

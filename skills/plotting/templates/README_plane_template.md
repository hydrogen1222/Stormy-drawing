# __FIGURE_NAME__

<!-- 这份说明给图的作者和以后重画这张图的 agent 看。用中文写，文件名保持英文。 -->

## 这张图想说明什么

（一句话。例如：LiDS 头基与表面 Li、O 之间没有 ELF 高值桥，是离子型接触。）

## 数据从哪来

| 数据文件（`data/` 内） | 来源机器 | 来源路径 | 怎么得到 |
|---|---|---|---|
| `plane.txt` | 机器名 | 完整路径 | Multiwfn 主功能 4，函数 ELF，`Export the current plane data to plane.txt` |
| `atoms.txt` | 机器名 | 完整路径 | 每行 `序号 元素 x y z`（Å），序号与 molden 一致 |

数据是复制来的，不是链接。

## 平面怎么定的

- 波函数文件（molden 的路径）：
- 定义平面的三个原子（按输入顺序，序号+元素）：
- 格点数、范围、Multiwfn 版本：
- 平面为什么选这三个原子（想看哪处接触）：

## 画图设置

- 数值：ELF，0 到 1，色标 Turbo，同组图（几处接触）必须同一色标范围
- 标出的原子：离平面不超过 `H_MAX`（默认 0.4 Å）的原子，自动标；`ORIGIN_ATOM`（若设）：
- 赝势说明：（CP2K 的 GTH 赝势里 Li 保留 1s²，会出现 ELF≈1 的圆盘，不是键；O、S、Cl、P 内层被赝势替掉，核处是低值小点）
- 色调模式：normal 和 soft 两份都在 `output/` 里；用户选用：（待选定后写在这里，并把 `plot.py` 里的 `MODES` 改成只画选定的那一个）

## 自查结果

（把 `output/normal/__FIGURE_NAME___normal_checks.txt` 和 `output/soft/__FIGURE_NAME___soft_checks.txt` 的内容贴在这里，再写一句亲眼看两份图后的结论，包括：原子标记是否落在 Multiwfn 图上同一位置。）

## 修改记录

| 日期 | 改了什么 | 为什么 | 旧版本在 |
|---|---|---|---|
|  | 首次绘制 |  |  |

# 晶体结构图

> 状态：OVITO 出图这一路可以直接用；VESTA 两种做法**都还没有实测**，第一次使用时必须在 Stormy 的电脑上验证，验证结果写回本文件。

每个结构图同样放在 `figures/NNN_.../` 里，数据就是复制进来的结构文件（通常是 CONTCAR）。

## 共同规矩

- 用弛豫后的结构（CONTCAR），不用初始 POSCAR。
- **正交投影**，不用透视（透视会让距离和层间距变形）。
- 白底；细线画晶胞；原子颜色读 `figures/_style/colors.json`，和其他图里的元素颜色一致。
- 配位多面体（例如 PS₄ 四面体）画成半透明，中心原子颜色。
- 对比几种结构时，视角、缩放、原子半径、多面体设置完全一致。
- README 写清：结构文件来源、视角方向（例如沿 [001]）、原子半径、成键截断距离、多面体设置。

## 做法一：OVITO 脚本出最终图片（默认）

用 OVITO 的 Python 接口（`pip install ovito` 或 conda 安装）。如果项目里同时装了 AI-Computational-Chemist，直接用它 `ovito` skill 里的渲染脚本和说明（`structure-rendering.md`）。按上面的共同规矩设置正交投影、颜色和半径。颜色从 `colors.json` 读取后传给 OVITO 的粒子类型颜色。

输出 PNG（白底）和透明底 PNG 各一份，600 DPI 对应的像素尺寸按 8 cm 宽算（约 1890 像素）。

OVITO 能否画半透明配位多面体，取决于安装的 OVITO 版本和许可，第一次使用时实测并记录在这里。

## 做法二：给 Stormy 一个能直接在 VESTA 里打开的版本（待实测）

**不要从零手写 .vesta 文件。** 这个格式没有正式公开的说明，以前 agent 手写的 .vesta 在 VESTA 里只显示一个晶胞框。

### 2a. 统一颜色：生成 VESTA 的 elements.ini（待实测）

VESTA 安装目录里的 `elements.ini` 存着每种元素的默认颜色和半径。按 `colors.json` 生成一份新的 `elements.ini`（只改颜色，半径保留 VESTA 原值），Stormy 备份原文件后替换一次。以后在 VESTA 里直接打开 CONTCAR，颜色就和其他图一致。

验证方法：替换后打开一个含 S 的结构，S 原子应是 `colors.json` 里 S 的颜色。

### 2b. 模板法（待实测）

1. Stormy 在 VESTA 里把一个真实结构调到满意（多面体、键、半径、视角），存成 .vesta，放在 `figures/_style/vesta_template.vesta`。
2. 以后画同类结构时，agent 复制模板，只替换其中的晶胞参数和原子坐标部分，样式部分原样保留。
3. Stormy 打开检查。如果出现"只有晶胞框"或原子错位，说明替换方式不对，停止使用这一做法并记录原因。

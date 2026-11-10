# 晶体结构图

> 状态：OVITO 出图这一路可以直接用；VESTA 两种做法**都还没有实测**，第一次使用时必须在用户自己的电脑上验证，验证结果写回本文件。下面“同一个结构画给用户挑”是实验性功能（`--structure`），用户还没挑过，哪个包最好看以用户的选择为准。

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

## 做法二：给用户一个能直接在 VESTA 里打开的版本（待实测）

**不要从零手写 .vesta 文件。** 这个格式没有正式公开的说明，以前 agent 手写的 .vesta 在 VESTA 里只显示一个晶胞框。

### 2a. 统一颜色：生成 VESTA 的 elements.ini（待实测）

VESTA 安装目录里的 `elements.ini` 存着每种元素的默认颜色和半径。按 `colors.json` 生成一份新的 `elements.ini`（只改颜色，半径保留 VESTA 原值），用户备份原文件后替换一次。以后在 VESTA 里直接打开 CONTCAR，颜色就和其他图一致。

验证方法：替换后打开一个含 S 的结构，S 原子应是 `colors.json` 里 S 的颜色。

### 2b. 模板法（待实测）

1. 用户在 VESTA 里把一个真实结构调到满意（多面体、键、半径、视角），存成 .vesta，放在 `figures/_style/vesta_template.vesta`。
2. 以后画同类结构时，agent 复制模板，只替换其中的晶胞参数和原子坐标部分，样式部分原样保留。
3. 用户打开检查。如果出现"只有晶胞框"或原子错位，说明替换方式不对，停止使用这一做法并记录原因。

## 同一个结构画给用户挑（实验性，`init_figure.py ... --structure`）

用户没指定软件，或想看哪个包好看时，用这一做法。`plot.py` 调 `figures/_style/pubstruct.py`，把同一个结构用所有能用的包各画一遍，normal 和 soft 两种色调各一套。图文件名 `<文件夹名>_<模式>_<包名>.png`，包名就是后缀，互不覆盖；`_packages.txt` 逐个写明 OK、SKIPPED（原因）或 FAILED（原因）。一个包跑不了不影响其他包。

| 包名后缀 | 是什么 | 画什么 | 需要什么 | 状态 |
|---|---|---|---|---|
| `raycast` | 自带 numpy 光线投射，正交投影，球和键都是真 3D 着色 | 晶体、分子 | 只要 ase、numpy | 已测 |
| `ase` | `ase.io.write` 的 png，平的圆盘，当对照 | 晶体、分子 | ase | 已测 |
| `povray` | ase 写场景，POV-Ray 光追 | 晶体、分子 | `povray` 程序 | **未测**，这台机器没有 |
| `ovito` | ovito 的 Tachyon 渲染，子进程里跑 | 晶体、分子 | `pip install ovito`，Linux 无头机器还要 Vulkan 驱动 | **未测**，这台机器没有 Vulkan，会自己跳过 |
| `jmol` | Jmol 脚本无界面出图 | 晶体、分子 | java，设 `JMOL_JAR` 或 `jmol` 在 PATH 里 | **未测**，视角旋转是近似写法，第一次使用要核对 |
| `materia` | Typst 包 `@preview/materia`（Python 包 `typst`） | 晶体、分子；矢量 svg、pdf | `pip install typst`，要联网下载 Typst 包 | 已测（Li₂S、LiDS） |
| `rdkit` | RDKit 二维骨架式 | 分子；svg | rdkit，SMILES 或 mol 文件 | 已测 |
| `typed-smiles` | Typst 包 `@preview/typed-smiles` | 分子；svg、pdf | `pip install typst`，SMILES | 已测 |

规矩和注意事项：
- 元素颜色读 `colors.json`，所以 raycast、ase、materia、ovito、jmol 的颜色和其他图一致；rdkit、typed-smiles 用化学惯例配色，不读登记文件。
- 球的大小只是画图用的：默认共价半径的 0.4 倍，`RADII` 可以按元素改。materia 只有一个整体半径系数，不能按元素改，默认会把 Li 画得比 S 大。
- 晶胞面上的原子会补周期镜像（和 VESTA 一样）；成键用 `BONDS` 给每对元素的截断，不给就自动（晶体里只连不同元素，分子里所有原子对都连）。
- 只给 SMILES 的分子，三维图用 RDKit 随机构象，报告里会写明，**不能当作计算结果**。
- LiS₄ 这类共边多面体在 Li₂S 里会糊成一片（materia 试过），不适合反萤石；多面体图要换结构再试。
- materia 能直接读 POSCAR、CIF，但这里统一由 ase 读入后用显式晶格和原子坐标交给它，避开它对 CIF 的限制（部分占位等）。
- 几百个原子的超胞（LPSC、P15Cl15 这类）画起来是否好看、速度如何，**还没试过**，第一次用时记在这里。

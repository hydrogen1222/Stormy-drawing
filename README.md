# Stormy-drawing

给 AI agent 用的科研绘图 skill。让 Claude Code、Codex、Qwen Code、Kimi、pi、opencode、Antigravity（agy）等 agent 画出 Origin 风格、可以直接投稿的图，并且每张图都能随时重画。Linux、macOS、Windows 都能用。

作者：**Stormy**（[@hydrogen1222](https://github.com/hydrogen1222)）与 **Claude**（Anthropic）。

> English summary: a skill that teaches AI coding agents to make publication-quality matplotlib figures in one fixed, Origin-like style (bold Arial, outward major and minor ticks, closed frame), and to keep every figure reproducible: one folder per figure holding the copied data, the `plot.py` that draws it, and a README recipe. Built for computational materials science (DOS, band structures, NEB barriers, RDF, MSD, Arrhenius plots, 2D maps), usable for any line plot. Install with `install.sh` (Linux, macOS) or `install.ps1` (Windows), see below.

## 它解决什么问题

- agent 画的图默认是 matplotlib 的样子：有网格线、刻度难看、字体不对。这里把样式一次定死：Arial 全加粗、刻度朝外且有主次刻度、闭合图框、柔和且色盲友好的配色。
- agent 喜欢把所有图片丢进一个文件夹，图和数据对不上。这里规定每张图一个文件夹，里面放复制来的数据、画图脚本和"配方"说明：哪一列是横轴、哪一列是纵轴、数据从哪个计算来。图不合格时，任何一个新开的 agent 都能照着重画。
- agent 说"画好了"但图有毛病。这里每次保存都会自动检查：字体、上下标是否用公式渲染、文字有没有被裁掉、图例有没有压住曲线。不过关的图不交给人看。

## 包含什么

```
skills/plotting/
  SKILL.md                    skill 正文（中文）：目录结构、画图和重画的步骤、全部样式规则、自查清单
  scripts/pubstyle.py         样式模块：样式、三种固定画布、坐标轴取整、图例避让、颜色登记、检查和保存
  scripts/init_figure.py      在项目里新建一个图文件夹
  templates/                  plot.py 和 README.md 模板
  references/figure-types.md  态密度、能带、能垒、径向分布函数、均方位移、阿伦尼乌斯图、二维色图、柱状图的约定
  references/setup.md         安装 Arial 字体和 Python 环境
  references/structures.md    晶体结构图（OVITO；VESTA 做法待实测）
  examples/demo_all_types.py  用假数据画出全部图型，也用来自测
install.sh                    安装脚本（Linux、macOS）
install.ps1                   安装脚本（Windows PowerShell）
tests/smoke_test.sh           安装和出图的自动测试（Linux、macOS）
tests/smoke_test.ps1          同上（Windows，也能在 macOS/Linux 的 pwsh 里跑）
```

## 安装

先把仓库克隆到任意位置（只需一次）：

```bash
git clone https://github.com/hydrogen1222/Stormy-drawing.git ~/src/Stormy-drawing
```

**装进某个课题项目（推荐）**：进入项目目录再运行。

```bash
cd ~/projects/你的课题
~/src/Stormy-drawing/install.sh
```

skill 会被复制到 `./.agents/skills/plotting`，并让 Claude Code（`.claude/skills`）、Qwen Code（`.qwen/skills`）、Codex、Kimi、pi、opencode、Antigravity 等都能找到。复制的好处是每个项目固定在安装时的版本，以后改了 skill 也不会悄悄改变老项目的图。

**和 AI-Computational-Chemist 一起用**：在同一个项目目录里两个都装上即可，顺序不限。两者共用 `.agents/skills/`，互不覆盖。

**Windows**：在 PowerShell 里做同样的事，脚本是 `install.ps1`，选项写法改成 `-Global`、`-Harness claude,codex`、`-Target`、`-Mode link`、`-AgentsMd`、`-Force`、`-DryRun`。Windows 默认不允许直接运行脚本，所以前面加 `powershell -ExecutionPolicy Bypass -File`（只对这一次运行生效，不改系统设置）：

```powershell
git clone https://github.com/hydrogen1222/Stormy-drawing.git $HOME\src\Stormy-drawing
cd C:\projects\你的课题
powershell -ExecutionPolicy Bypass -File $HOME\src\Stormy-drawing\install.ps1
```

Windows 上默认复制，不需要管理员权限，也不需要打开"开发者模式"；`-Mode link` 用目录联接（junction）代替符号链接，同样不需要管理员权限。

**全局安装**（对你所有项目生效）：

```bash
~/src/Stormy-drawing/install.sh --global                      # 所有支持的 agent
~/src/Stormy-drawing/install.sh --global --harness claude,codex
```

**其他 agent**：把 skill 装进它的 skill 文件夹。

```bash
~/src/Stormy-drawing/install.sh --target /path/to/that/agent/skills
```

常用选项：`--agents-md` 在项目的 `AGENTS.md` 里加一段说明，让不会自动发现 skill 的 agent 也知道画图要读它；`--mode link` 用链接代替复制，`git pull` 后所有安装同时更新；`--force` 覆盖已有安装；`--dry-run` 只显示要做什么。完整说明见 `./install.sh --help`。

装好后重启或刷新 agent，让它重新读取 skill。

## 第一次在某台机器上画图

1. **Arial 字体**。Windows 和 macOS 自带，不用管。Linux 服务器上要装一次：Arial 是商业字体，不能随仓库分发，从 Windows 的 `C:\Windows\Fonts\` 拷出 `arial.ttf`、`arialbd.ttf`、`ariali.ttf`、`arialbi.ttf`，放进服务器的 `~/.local/share/fonts/`，再清掉 matplotlib 的字体缓存。不需要管理员权限，步骤见 `skills/plotting/references/setup.md`。没有 Arial 时脚本会直接报错，不会偷偷换字体。
2. **Python 环境**：需要 `matplotlib>=3.8` 和 `numpy`。有 [uv](https://docs.astral.sh/uv/) 的话直接 `uv run plot.py`。

## 测试

```bash
sh tests/smoke_test.sh                              # 机器上有 Arial 时
PUBSTYLE_ALLOW_STANDIN=1 sh tests/smoke_test.sh     # 没有 Arial 时，用字宽相同的替身字体测试
```

Windows：

```powershell
powershell -ExecutionPolicy Bypass -File tests\smoke_test.ps1
```

## 引用和许可

本仓库使用 MIT 许可证，见 `LICENSE`。引用信息见 `CITATION.cff`。

这里的规矩是 Stormy 和 Claude 在 2026 年 10 月逐条讨论定下的；skill 里标为"待实测"的部分（VESTA 相关做法）还没有在真实数据上验证。

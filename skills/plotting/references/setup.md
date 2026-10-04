# 第一次在某台机器上画图

每台机器做一次。Linux 服务器、Windows 电脑、Mac 都能用，区别只在字体这一步。做完后在服务器的 `~/.cluster-agents.md` 里记一行"Arial 已安装、matplotlib 可用"，以后不用再查（个人电脑上不用记）。

## 1. 准备 Arial

先检查 matplotlib 能不能找到 Arial（三种系统都用这一行，Windows 上把 `python` 换成你平时用的 Python）：

```bash
python -c "from matplotlib import font_manager as f; print('Arial' in {x.name for x in f.fontManager.ttflist})"
```

打印 `True` 就跳过这一节。

**Windows 和 macOS**：系统自带 Arial（Windows 在 `C:\Windows\Fonts\`，macOS 在 `/System/Library/Fonts/Supplemental/`），一般直接是 `True`。如果是 `False`，多半是 matplotlib 的字体缓存旧了，删掉缓存后再检查一次：

```bash
python -c "import matplotlib, pathlib; [p.unlink() for p in pathlib.Path(matplotlib.get_cachedir()).glob('fontlist-*.json')]"
```

**Linux 服务器**（不需要管理员权限）：Arial 是商业字体，不能随仓库分发，需要 Stormy 从自己的 Windows 电脑提供一次 `C:\Windows\Fonts\` 下的 `arial.ttf`（常规）、`arialbd.ttf`（粗体）、`ariali.ttf`（斜体）、`arialbi.ttf`（粗斜体），传到服务器任意位置，告诉 agent 路径。agent 执行：

```bash
mkdir -p ~/.local/share/fonts
cp /path/to/arial*.ttf ~/.local/share/fonts/
fc-cache -f ~/.local/share/fonts 2>/dev/null || true
python -c "import matplotlib, pathlib; [p.unlink() for p in pathlib.Path(matplotlib.get_cachedir()).glob('fontlist-*.json')]"
```

再运行开头那行检查，打印 `True` 才算装好。

找不到 Arial 时 `pubstyle.apply()` 会直接报错。**不许**为了让脚本跑通而改成别的字体。只有在 Stormy 同意先出草稿时，才可以设环境变量 `PUBSTYLE_ALLOW_STANDIN=1`（Linux/macOS：`export PUBSTYLE_ALLOW_STANDIN=1`；Windows PowerShell：`$env:PUBSTYLE_ALLOW_STANDIN = "1"`），用字宽相同的 Liberation Sans 代替；这样画出的图在检查结果里标为草稿，正式图必须重画。

## 2. Python 环境

需要 Python 3.10 以上、`matplotlib>=3.8` 和 `numpy`。Windows 上命令一般是 `python`（或 `py`），Linux 和 macOS 上 `python` 不存在时用 `python3`。优先用 `uv run plot.py`（`plot.py` 开头已按 PEP 723 声明依赖，uv 会自动准备独立环境）；没有 uv 时用已有的 conda 环境，`python plot.py`。

检查：

```bash
python -c "import matplotlib, numpy; print(matplotlib.__version__, numpy.__version__)"
```

## 3. 项目里的样式文件

不需要手动做。第一次在某个项目里运行 `scripts/init_figure.py` 时，会自动建 `figures/_style/pubstyle.py` 和空的 `colors.json`。

本 skill 的 `scripts/pubstyle.py` 以后更新了，已有项目不会自动跟着变（这是有意的，保证同一项目里的图风格一致）。要更新某个项目，先问 Stormy，再把新版复制到该项目的 `figures/_style/`，然后重画该项目的全部图。

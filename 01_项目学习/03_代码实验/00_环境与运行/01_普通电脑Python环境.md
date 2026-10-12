# 普通电脑 Python 环境

示例以Python 3.10或更新解释器编写。电脑上的 `python` 和本任务使用的解释器可能不同，先用 `python --version` 与 `python -c "import sys; print(sys.executable)"` 查看。

本次只读清点：Codex提供的Python 3.12.14已有NumPy 2.3.5，尚未安装SciPy与Matplotlib；用户默认解释器另位于Miniconda。未安装依赖不代表代码已经能在此环境运行。

PowerShell中新建独立环境的操作（由学习者需要时执行）：

```powershell
python -m venv .venv-learning
.\.venv-learning\Scripts\python.exe -m pip install numpy scipy matplotlib
```

标准库实验无需安装这三项。数值章节用NumPy；LQR和优化还用SciPy。Matplotlib只用于图，不是所有实验必需。安装后记录实际版本，不把本次NumPy版本当作所有库的通用兼容保证。

运行独立脚本时给路径加引号：

```powershell
python '01_项目学习/03_代码实验/01_基础实验/01_矩阵方程与伪逆/lab.py' --out-dir '我的实验结果/矩阵'
```

上例从 `F:/27fall/申请材料` 执行。输出目录是学习数据，不是原项目配置。脚本未交付前见重构清单，不能运行不存在的入口。

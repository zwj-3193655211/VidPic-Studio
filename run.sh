#!/bin/bash
# 多角度人脸生成器 - 一键启动脚本 (Linux/macOS/Git-Bash)
# 修复: LF 行尾 / 完整依赖检查 / 优先虚拟环境
cd "$(dirname "$0")"

echo "================================================"
echo "  多角度人脸生成器 v0.2.0 - 一键启动"
echo "================================================"
echo ""

# 优先项目虚拟环境，否则用全局 python3
PY=python3
if [ -x ".venv/bin/python" ]; then
    PY=.venv/bin/python
    echo "[使用虚拟环境 .venv]"
else
    echo "[使用全局 Python]"
fi

# 检查 Python
if ! "$PY" --version &>/dev/null; then
    echo "错误：未找到 Python，请先安装 Python 3.10+"
    exit 1
fi

# 检查核心依赖
if ! "$PY" -c "import gradio, torch, diffusers, transformers, PIL" &>/dev/null; then
    echo "核心依赖缺失，正在安装（可能需要几分钟）..."
    "$PY" -m pip install -r requirements.txt || { echo "错误：依赖安装失败"; exit 1; }
    if ! "$PY" -c "import gradio, torch, diffusers, transformers, PIL" &>/dev/null; then
        echo "错误：依赖安装后仍无法导入，请手动排查"
        exit 1
    fi
fi

echo ""
echo "正在启动应用..."
echo "浏览器将打开: http://127.0.0.1:7860"
echo "提示：首次点击\"生成\"会下载 Stable Diffusion 模型（约 5GB）"
echo ""
"$PY" app.py

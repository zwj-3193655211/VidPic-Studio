#!/bin/bash
# Launch script for Face Generator Application (Linux/Mac)

echo "================================================"
echo "  多角度人脸生成器 - 启动脚本"
echo "================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python，请先安装Python 3.10+"
    exit 1
fi

# Check if dependencies are installed
python3 -c "import gradio" &> /dev/null
if [ $? -ne 0 ]; then
    echo "依赖未安装，正在安装..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "错误：依赖安装失败"
        exit 1
    fi
fi

# Launch the application
echo ""
echo "正在启动应用..."
echo "应用将在浏览器中打开: http://127.0.0.1:7860"
echo ""
python3 app.py

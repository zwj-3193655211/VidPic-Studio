@echo off
REM Launch script for Face Generator Application (Windows)

echo ================================================
echo   多角度人脸生成器 - 启动脚本
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import gradio" >nul 2>&1
if errorlevel 1 (
    echo 依赖未安装，正在安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误：依赖安装失败
        pause
        exit /b 1
    )
)

REM Launch the application
echo.
echo 正在启动应用...
echo 应用将在浏览器中打开: http://127.0.0.1:7860
echo.
python app.py

pause

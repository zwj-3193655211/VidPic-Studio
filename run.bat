@echo off
REM ================================================
REM   AI 图片生成器 v0.3.1 - 一键启动 (Windows)
REM   修复: ANSI/GBK 编码 + CRLF 换行 / Anaconda 解释器 / 模型检测用 models_registry
REM   注意：本文件必须保持 ANSI/GBK 编码 + CRLF 换行，否则 cmd 解析会出错
REM ================================================

setlocal
chcp 936 >nul
cd /d "%~dp0"

echo ================================================
echo   AI 图片生成器 v0.3.1 - 一键启动
echo ================================================
echo.

REM ---- 选择 Python：Anaconda py310_env 优先，项目 .venv 备选，PATH 兜底 ----
set "PYTHON="
if exist "D:\tools\Anaconda3\envs\py310_env\python.exe" (
    set "PYTHON=D:\tools\Anaconda3\envs\py310_env\python.exe"
    echo [Python: Anaconda py310_env（推荐，CUDA torch 兼容 RTX 5060）]
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
    echo [Python: 项目 .venv]
) else (
    set "PYTHON=python"
    echo [Python: PATH 中的 python]
)

REM ---- 检查 Python 是否可用 ----
"%PYTHON%" --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到 Python，请先安装 Anaconda 或 Python 3.10+
    pause
    exit /b 1
)

REM ---- 模型检测：调用 models_registry 实际判断每个模型的 path 是否存在 ----
"%PYTHON%" -c "from models_registry import MODELS, _m, available_models; import os; rows=[(k, v['name'], os.path.exists(v['path'])) for k,v in MODELS.items()]; print('  [模型] 路径检测结果：'); [print('   ', ('OK ' if ok else 'X  '), k.ljust(10), name) for k, name, ok in rows]; print('  [模型] 可用：', [k for k,_,ok in rows if ok] or '无')"
if errorlevel 1 (
    echo [模型] 检测脚本失败，将按需在线下载
) else (
    echo.
)

REM ---- 检查核心依赖 ----
"%PYTHON%" -c "import gradio, torch, diffusers, transformers, PIL" >nul 2>&1
if errorlevel 1 (
    echo 核心依赖缺失，正在安装（可能需要几分钟）...
    "%PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误：依赖安装失败，请检查网络或手动排查
        pause
        exit /b 1
    )
    "%PYTHON%" -c "import gradio, torch, diffusers, transformers, PIL" >nul 2>&1
    if errorlevel 1 (
        echo 错误：依赖安装后仍无法导入，请手动运行 pip 排查
        pause
        exit /b 1
    )
)

REM ---- 显示 GPU 状态 ----
"%PYTHON%" -c "import torch; print('[GPU]', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda, CPU mode')" 2>nul

echo.
echo 正在启动应用...
echo 本地地址: http://127.0.0.1:7860
echo 关闭本窗口或 Ctrl+C 停止应用
echo.

"%PYTHON%" app.py

echo.
echo 应用已退出。
pause
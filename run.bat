@echo off
REM ================================================
REM   AI 图片生成器 - 一键启动脚本 (Windows)
REM   修复: GBK编码 / 完整依赖检查 / 模型下拉 / venv优先
REM   注意: if 块内 echo 不能用英文括号，否则 cmd 语法错误
REM ================================================

setlocal
cd /d "%~dp0"

echo ================================================
echo   AI 图片生成器 v0.3.0 - 一键启动
echo ================================================
echo.

REM ---- 选择 Python：项目 venv 优先（transformers 4.x + CUDA torch），
REM      其次 Anaconda（全局 CUDA torch），最后 PATH 中的 python ----
set "PYTHON=python"
if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
    echo [Python: .venv，项目虚拟环境]
) else (
    if exist "D:\tools\Anaconda3\python.exe" (
        set "PYTHON=D:\tools\Anaconda3\python.exe"
        echo [Python: Anaconda，全局环境]
    ) else (
        echo [Python: PATH 中的 python]
    )
)

REM ---- 本地模型检测（models/ 目录，models_registry 自动管理，免联网）----
set "MODEL_ARGS="
if exist "models\sd15\model_index.json" (
    echo [模型：本地模型已就绪（models/ 下 sd15、sdxl_base、moyu_xl、realvisxl）]
) else (
    echo [模型：未检测到本地模型，首次生成需在线下载]
)

REM ---- 网络说明：本地推理无需联网。如需在线下载模型，请直连 hf-mirror ----
REM 不要设置本地代理（clash 代理是坏的），下载时用：
REM   set "HF_ENDPOINT=https://hf-mirror.com"

REM ---- 检查 Python 是否可用 ----
"%PYTHON%" --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

REM ---- 检查核心依赖（gradio/torch/diffusers/transformers/PIL）----
"%PYTHON%" -c "import gradio, torch, diffusers, transformers, PIL" >nul 2>&1
if errorlevel 1 (
    echo 核心依赖缺失，正在安装（可能需要几分钟）...
    "%PYTHON%" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误：依赖安装失败，请检查网络后重试
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

REM ---- 显示 GPU 状态（仅提示，不阻断）----
"%PYTHON%" -c "import torch; print('[GPU]', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda, CPU mode')" 2>nul

echo.
echo 正在启动应用...
echo 浏览器将打开: http://127.0.0.1:7860
echo 关闭本窗口或按 Ctrl+C 可停止应用
echo.

"%PYTHON%" app.py %MODEL_ARGS%

echo.
echo 应用已退出。
pause

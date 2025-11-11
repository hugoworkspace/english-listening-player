@echo off
chcp 65001 >nul
echo ========================================
echo   英语精听复读软件启动器
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.6+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查Python依赖...
python -c "import PyQt5, vlc, pysrt" >nul 2>&1
if errorlevel 1 (
    echo 正在安装必要的Python包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖安装失败，请手动运行: pip install -r requirements.txt
        pause
        exit /b 1
    )
)

REM 检查VLC是否安装
echo 检查VLC播放器...
python -c "import vlc" >nul 2>&1
if errorlevel 1 (
    echo.
    echo 警告: VLC播放器可能未正确安装
    echo 请确保已安装VLC媒体播放器
    echo 下载地址: https://www.videolan.org/vlc/
    echo.
    echo 按任意键继续启动软件...
    pause >nul
)

REM 启动应用程序
echo.
echo 正在启动英语精听复读软件...
echo.
python english_listening_player.py

if errorlevel 1 (
    echo.
    echo 启动失败，请检查:
    echo 1. 是否已安装VLC播放器
    echo 2. Python依赖是否完整
    echo 3. 系统环境变量设置
    pause
)

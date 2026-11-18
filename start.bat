@echo off
chcp 936 >nul
cd /d "%~dp0"

rem ============================================================
rem 使用方法
rem ------------------------------------------------------------
rem 双击 start.bat，或在本目录执行：
rem   start.bat
rem
rem 脚本会激活 Conda 环境 ios-device，然后运行：
rem   python main.py "南区田径场800m-smooth.gpx"
rem
rem 自定义等待点：
rem   start.bat --start 31.23990 121.49583
rem
rem 启动后会先设置固定定位，按 Enter 才开始沿 GPX 移动。
rem 按 Ctrl+C 停止并恢复真实定位。
rem
rem 其他电脑或其他环境：
rem 1. 将下方 activate.bat 的完整路径改成该电脑实际的 Conda 路径。
rem    常见位置：
rem      C:\Users\你的用户名\miniconda3\Scripts\activate.bat
rem      C:\Users\你的用户名\anaconda3\Scripts\activate.bat
rem      C:\ProgramData\miniconda3\Scripts\activate.bat
rem 2. 将 ios-device 改成该电脑实际使用的 Conda 环境名称。
rem 3. 环境中需要安装 Python 3.13 和 pymobiledevice3：
rem      python -m pip install -U pymobiledevice3
rem 4. 如果使用 Anaconda Prompt、venv 或其他 Python 环境，
rem    可以先手动激活环境，再单独运行：
rem      python main.py "南区田径场800m-smooth.gpx"
rem 5. macOS/Linux 不能直接运行 .bat，需要在终端激活 Conda 后执行：
rem      python main.py "南区田径场800m-smooth.gpx"
rem 6. 使用系统级 Python：
rem    先确认当前 python 指向系统解释器并检查版本：
rem      where python
rem      python --version
rem    安装依赖：
rem      python -m pip install -U pymobiledevice3
rem    然后注释或删除下方的 Conda activate 命令，使脚本直接调用
rem    系统级 python。需要恢复 Conda 时再取消该行注释。
rem ============================================================

call C:\ProgramData\miniconda3\Scripts\activate.bat ios-device
python main.py "南区田径场800m-smooth.gpx" %*

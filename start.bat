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
rem   python main.py "*.gpx"
rem
rem 启动后会先设置固定定位，按 Enter 才开始沿 GPX 移动。
rem 等待点固定为 GPX 的第一个轨迹点。
rem 路线完成后会固定在最后一个点，再按 Enter 结束并恢复真实定位。
rem 按 Ctrl+C 可以在任意阶段立即退出。
rem
rem 其他电脑或其他环境：
rem Python:
rem 1. 使用 Conda:
rem    确保环境中已安装了所需的依赖。
rem    (1) 将下方 activate.bat 的完整路径改成该电脑实际的 Conda 路径。
rem         常见位置：
rem         C:\Users\你的用户名\miniconda3\Scripts\activate.bat
rem         C:\Users\你的用户名\anaconda3\Scripts\activate.bat
rem         C:\ProgramData\miniconda3\Scripts\activate.bat
rem    (2) 将 ios-device 改成该电脑实际使用的 Conda 环境名称。
rem 2. 使用系统级 Python：
rem    确保环境中已安装了所需的依赖。
rem    注释或删除下方的 Conda activate 命令，使脚本直接调用
rem    系统级 python。需要恢复 Conda 时再取消该行注释。
rem 3. 如果使用 Anaconda Prompt、venv 或其他 Python 环境，
rem    可以先手动激活环境，再单独运行：
rem      python main.py "*.gpx"
rem 4. macOS/Linux 不能直接运行 .bat，需要在终端激活 Conda 后执行：
rem      python main.py "*.gpx"
rem
rem GPX 文件:
rem 将引号内的 gpx 文件路径修改为你需要使用的 gpx 文件路径。
rem ============================================================

call C:\ProgramData\miniconda3\Scripts\activate.bat ios-device
python realistic_gpx.py "./examples/南区田径场800m-4m22s-smooth.gpx" -o "./examples/南区田径场800m-4m22s-smooth-realistic.gpx" --max-offset 2.5 --correlation 8
python main.py "./examples/南区田径场800m-4m22s-smooth-realistic.gpx"
pause
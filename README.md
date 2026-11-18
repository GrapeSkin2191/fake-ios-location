# iOS GPX 虚拟定位路线回放

通过 `pymobiledevice3` 将连接的 iPhone 设置到指定位置，并按照 GPX 轨迹和时间戳移动。启动后先进入固定等待点，按 Enter 开始移动，按 `Ctrl+C` 停止并恢复真实定位。

自带南区田径场路径（2 圈，即 800 米），可用于刷锻！

本项目由 Codex (powered by Deepseek) 协助完成。

## 环境要求

- Windows 10/11、iOS 17+
- Python 3.13
- iTunes 或 Apple Devices
- iPhone 已解锁、信任电脑并开启开发者模式

## 安装

使用 Conda：

```powershell
conda create -n ios-device python=3.13 -y
conda activate ios-device
python -m pip install -U pymobiledevice3
```

或使用系统级 Python：

```powershell
python --version
python -m pip install -U pymobiledevice3
```

## 准备 GPX

项目中已有南区田径场 800m 路径，如需要其他路径可按以下说明自行创建。

GPX 需要包含 `<trkpt>` 和递增的 `<time>`。可使用 [gpx.studio](https://gpx.studio/app) 规划路线并按固定速度生成时间戳。

轨迹点太少时会跳点，可使用项目中的脚本加密：

```powershell
python densify_gpx.py "输入路线.gpx" -o "输出路线-smooth.gpx" --interval 1
```

`--interval 1` 表示相邻点最多间隔 1 秒。

## 运行

Windows 下，运行 `start.bat`（大概率需要先调整 bat 中的 python 路径）；

或直接运行（确保你调用的 `python` 有正确的环境）：

```powershell
python main.py "南区田径场800m-smooth.gpx"
```

默认等待点为 GPX 第一个轨迹点，也可指定：

```powershell
python main.py "南区田径场800m-smooth.gpx" --start 31.23990 121.49583
```

其他电脑使用 `start.bat` 时，需要修改其中的 Conda 激活路径和环境名称。

## 文件

- `main.py`：连接 iPhone 并回放 GPX
- `densify_gpx.py`：加密 GPX 轨迹点
- `start.bat`：Windows 快速启动脚本
- `南区田径场800m-smooth.gpx`：示例路线

## 常见问题

- 提示 userspace tunnel：属于正常信息，继续等待连接完成。
- 手机无法识别：检查 USB 线、Apple 驱动、解锁状态和设备信任。
- GPX 没有轨迹点：确保使用 `<trkpt>`，不是只有 `<rtept>`。
- 移动仍跳点：使用 `densify_gpx.py` 减小点的时间间隔。
- 速度不正确：检查 GPX 时间戳是否完整、递增并按固定速度生成。

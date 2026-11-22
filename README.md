# iOS GPX 虚拟定位路线回放

通过 `pymobiledevice3` 将连接的 iPhone 设置到指定位置，并按照 GPX 轨迹和时间戳移动。

本项目由 Codex (powered by Deepseek) 协助完成。

路线模拟功能的使用具体说明见 [README_GPX.md](./README_GPX.md)。

## 环境要求

- Windows 10/11、iOS 17+（Mac 理论可行，但未经测试）
- Python 3.13（其他 Python 版本也可行，但未经测试，可能需要调整代码）
- iTunes 或 Apple Devices
- iPhone 已解锁、信任电脑并开启开发者模式

默认需要使用数据线连接手机和电脑。

也可以通过 Wi-Fi 连接，见 [使用 Wi-Fi 连接](#使用-wi-fi-连接)

## 安装

使用 Conda：

```powershell
conda create -n ios-device python=3.13 -y
conda activate ios-device
python -m pip install -U pymobiledevice3
```

其中的 `ios-device` 可以修改为你想要的环境名称。

或使用系统级 Python：

```powershell
python --version
python -m pip install -U pymobiledevice3
```

## 使用 Wi-Fi 连接

如果要在不打开 Apple Devices 的情况下通过 Wi-Fi 运行，需要先通过 USB
完成一次 RemotePairing 初始化：

```powershell
python -m pymobiledevice3 lockdown remotepairing --pair --udid 你的设备UDID
```

完成后可拔掉 USB，并指定手机在当前局域网中的 IPv4 地址运行（可以用下面的语句替换启动脚本中的对应语句）：

```powershell
python run_gpx.py "你的gpx文件.gpx" --wireless --udid 你的设备UDID --wireless-host 192.168.1.113
```

也可以省略 `--wireless-host`，让程序通过 Bonjour 自动发现手机。存在 VPN
虚拟网卡时建议明确指定局域网 IPv4 地址，避免连接到虚拟网卡公布的地址。

## 文件

- `run_gpx.py`：连接 iPhone 并回放 GPX
- `densify_gpx.py`：加密 GPX 轨迹点
- `realistic_gpx.py`：为轨迹加入连续低幅 GPS 漂移
- `start_gpx.bat`：路线模拟 Windows 快速启动脚本
- `./examples`：示例路线
- `README_GPX.md`：GPX 路线模拟详细说明

## 常见问题

- 提示 userspace tunnel：属于正常信息，继续等待连接完成。
- 手机无法识别：检查 USB 线、Apple 驱动、解锁状态和设备信任。
- Wi-Fi 提示 RemotePairing 连接失败：确认已完成一次 USB
  `lockdown remotepairing --pair`，并尝试用 `--wireless-host` 指定手机 IP。

路线和 GPX 相关的问题见 [README_GPX.md](./README_GPX.md#常见问题)。

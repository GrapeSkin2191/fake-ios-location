# GPX 路线模拟说明

本文介绍 GPX 路线文件的准备、轨迹优化、启动与中止路线模拟，以及常见问题。

## 运行流程

启动后先进入固定等待点，按 `Enter` 开始移动；路线完成后定位固定在最后一点，
再按 `Enter` 结束并恢复真实定位。

路线执行过程中可以按 `Ctrl+C` 中止。程序会执行定位清理并恢复 iPhone 的真实定位。
如果从批处理脚本启动，控制台可能提示“终止批处理操作(Y/N)?”，输入 `Y` 即可。
不要连续多次按 `Ctrl+C`，以免中断定位清理。

项目自带南区田径场路径（2 圈，即 800 米），位于 `./examples`。

## 准备 GPX

如需自行创建路线，GPX 中需要包含 `<trkpt>` 和递增的 `<time>`。可以使用
[gpx.studio](https://gpx.studio/app) 规划路线并按固定速度生成时间。

轨迹点太少时会出现跳点，可使用项目中的脚本加密：

```powershell
python densify_gpx.py "输入路线.gpx" --interval 1
```

默认输出文件名为 `输入路线-smooth.gpx`；`--interval 1` 表示相邻点最多间隔
1 秒。

如需在轨迹上加入连续、低幅度的 GPS 漂移，同时保持时间戳不变：

```powershell
python realistic_gpx.py "输入路线.gpx" --max-offset 2 --correlation 9
```

默认输出文件名为 `输入路线-realistic.gpx`；`--max-offset 2` 表示最多偏移
2 米，`--correlation` 越大，偏移点越少。

## 启动路线

Windows 下可以运行 `start_gpx.bat`。首次使用前需要检查 bat 中的 Python
路径和 GPX 文件路径，具体位置见脚本中的注释。

也可以直接运行以下命令，并确保当前 `python` 属于正确的 Conda 环境：

```powershell
python run_gpx.py "你的gpx文件.gpx"
```

## 常见问题

- GPX 没有轨迹点：确保使用 `<trkpt>`，不是只有 `<rtept>`。
- 移动仍跳点：使用 `densify_gpx.py` 减小相邻点的时间间隔。
- 速度不正确：检查 GPX 时间戳是否完整、递增，并按目标速度生成。
- 按 `Ctrl+C` 后出现 `KeyboardInterrupt`：这是 Python 收到中断信号的正常提示，
  不属于路线执行错误。

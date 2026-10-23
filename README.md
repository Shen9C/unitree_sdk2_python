# unitree_sdk2py

宇树（Unitree）机器人官方 Python SDK 的仓库说明。基于 Eclipse CycloneDDS 提供两类能力：

- **高层控制**：通过 RPC 调用机器人内置运控/视频/音频等服务（`rt/api/<service>/request|response`）。
- **低层控制**：直接订阅状态、发布关节指令（`rt/lowstate` / `rt/lowcmd` 等），需自行实现控制律与 CRC。

> 架构细节、模块职责、调用时序、机型服务矩阵与风险清单见 [ARCHITECTURE.md](ARCHITECTURE.md)。
> 本仓库处于「遗留系统改造」阶段，改造规范见 [AGENTS.md](AGENTS.md)，接口冻结基线见 [contracts/](contracts/README.md)。

---

## 一、技术栈

| 项 | 说明 |
| :-- | :-- |
| 语言 | Python >= 3.8（开发环境 3.10） |
| 通信 | `cyclonedds == 0.10.2`（固定版本） |
| 数据模型 | IDL 生成类：`unitree_go`（20 电机）、`unitree_hg`（35 电机）、`unitree_api`（RPC 报文） |
| 依赖库 | `numpy`、`opencv-python`；手柄示例另需 `pygame`（**未写入依赖声明**） |
| 平台相关 | CRC 加速 `.so` 与 `timerfd` 周期线程仅 Linux 可用 |
| 打包 | setuptools + `pyproject.toml`（包名 `unitree_sdk2py`，版本 1.0.1，BSD-3-Clause） |

---

## 二、安装

### 依赖

- Python >= 3.8
- cyclonedds == 0.10.2
- numpy
- opencv-python

### 源码安装

```bash
cd ~
sudo apt install python3-pip
git clone https://github.com/unitreerobotics/unitree_sdk2_python.git
cd unitree_sdk2_python
pip3 install -e .
```

### FAQ：`Could not locate cyclonedds`

```bash
Could not locate cyclonedds. Try to set CYCLONEDDS_HOME or CMAKE_PREFIX_PATH
```

先编译安装 cyclonedds：

```bash
cd ~
git clone https://github.com/eclipse-cyclonedds/cyclonedds -b releases/0.10.x
cd cyclonedds && mkdir build install && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=../install
cmake --build . --target install
```

再指定路径安装本包：

```bash
cd ~/unitree_sdk2_python
export CYCLONEDDS_HOME=~/cyclonedds/install
pip3 install -e .
```

参考：https://pypi.org/project/cyclonedds/#installing-with-pre-built-binaries

---

## 三、目录结构

```
unitree_sdk2py/            SDK 主体
├── core/                  DDS 通道层（ChannelFactory / ChannelPublisher / ChannelSubscriber）
├── rpc/                   RPC 层（Client / Server / Future / Lease / 错误码）
├── idl/                   DDS 数据模型（unitree_go / unitree_hg / unitree_api）
├── utils/                 工具（Future、BQueue、周期线程、CRC、单例、手柄、Hz 统计）
├── comm/motion_switcher/  运控模式切换
├── go2/ b2/ b2w/ go2w/    四足机型服务客户端
├── g1/ h1/ h2/ h1_2/      人形机型服务客户端
├── a2/ as2/ r1/           其他机型
└── test/                  手工验证脚本（非自动化测试）
example/                   按机型组织的可运行示例（共 53 个 .py）
```

---

## 四、快速开始

### 1. 初始化 DDS（所有示例的第一步）

```python
from unitree_sdk2py.core.channel import ChannelFactoryInitialize

ChannelFactoryInitialize(0)              # 自动选择网卡
# 或指定网卡（机器人直连场景常用）
# ChannelFactoryInitialize(0, "eth0")
```

`ChannelFactoryInitialize(id, networkInterface)` 为全局单例初始化，**每个进程只能调用一次且不可重配**。

### 2. 高层控制

```bash
python3 example/go2/high_level/go2_sport_client.py eth0
```

示例内部逻辑：

```python
from unitree_sdk2py.go2.sport.sport_client import SportClient

client = SportClient()
client.SetTimeout(10.0)
client.Init()
client.Move(0.3, 0.0, 0.0)   # x, y, yaw
client.StopMove()
```

可用机型与示例：

| 机型 | 高层示例 |
| :-- | :-- |
| Go2 | `example/go2/high_level/go2_sport_client.py`、`go2_utlidar_switch.py` |
| Go2W | `example/go2w/high_level/go2w_sport_client.py` |
| B2 / B2W | `example/b2/high_level/b2_sport_client.py`、`example/b2w/high_level/b2w_sport_client.py` |
| A2 | `example/a2/sport/a2_sport_client.py`、`a2_sport_state.py` |
| AS2 | `example/as2/sport/as2_sport_client.py`、`as2_sport_state.py` |
| G1 | `example/g1/high_level/g1_loco_client_example.py`、`g1_arm_action_example.py`、`g1_arm5_sdk_dds_example.py`、`g1_arm7_sdk_dds_example.py` |
| H1 | `example/h1/high_level/h1_loco_client_example.py` |
| H2 | `example/h2/high_level/h2_loco_client_example.py`、`h2_arm_sdk_dds_example.py` |
| R1 | `example/r1/high_level/r1_loco_client_example.py` |

### 3. 低层控制

低层示例直接读写 DDS topic 并计算 CRC，**必须运行在 Linux 机器人端**：

```bash
python3 example/h1/low_level/h1_low_level_example.py
```

核心步骤（以 H1 为例）：

```python
from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber
from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_, LowState_
from unitree_sdk2py.utils.crc import CRC

low_state_sub = ChannelSubscriber("rt/lowstate", LowState_)
low_state_sub.Init(handler, 10)
low_cmd_pub = ChannelPublisher("rt/lowcmd", LowCmd_)
low_cmd_pub.Init()

# 进入低层控制前先切换到 normal 模式
from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import MotionSwitcherClient
msc = MotionSwitcherClient()
msc.CheckMode()
msc.ReleaseMode()
```

- 周期任务推荐 `RecurrentThread`（依赖 Linux `timerfd`）。
- 每条 `LowCmd` 必须写入正确 CRC：`cmd.crc = CRC().Crc(cmd)`。
- CRC 结构体格式固定：LowCmd 812B、LowState 1180B、HGLowCmd 1004B、HGLowState 2092B，字段变更会导致静默错位。

对应示例：

| 机型 | 低层示例 |
| :-- | :-- |
| Go2 / Go2W | `example/go2/low_level/go2_stand_example.py`、`example/go2w/low_level/go2w_stand_example.py` |
| B2 / B2W | `example/b2/low_level/b2_stand_example.py`、`example/b2w/low_level/b2w_stand_example.py` |
| G1 | `example/g1/low_level/g1_low_level_example.py` |
| H1 | `example/h1/low_level/h1_low_level_example.py` |
| H1-2 | `example/h1_2/low_level/h1_2_low_level_example.py` |
| H2 | `example/h2/low_level/h2_ankle_swing_example.py` |
| R1 | `example/r1/low_level/r1_low_level_example.py`（A5/A7 各一份） |

### 4. 运控模式切换

```bash
python3 example/motionSwitcher/motion_switcher_example.py eth0
```

```python
from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import MotionSwitcherClient

msc = MotionSwitcherClient()
msc.Init()
code, mode = msc.CheckMode()
code, _ = msc.SelectMode("normal")   # ai / normal / advanced / ai-w 等，取决于机型
msc.ReleaseMode()
```

### 5. 视频 / 摄像头

| 场景 | 示例 |
| :-- | :-- |
| Go2 前置摄像头 | `example/go2/front_camera/camera_opencv.py`、`capture_image.py` |
| B2 / B2W 摄像头 | `example/b2/camera/camera_opencv.py`、`example/b2w/camera/camera_opencv.py` |

```python
from unitree_sdk2py.go2.video.video_client import VideoClient

client = VideoClient()
code, data = client.GetImageSample()   # data 为 JPEG 字节流
```

### 6. 其他示例

| 功能 | 示例 |
| :-- | :-- |
| DDS 收发最小示例 | `example/helloworld/publisher.py`、`subscriber.py` |
| 语音/音量 | `example/vui_client/vui_client_example.py` |
| 音频播放 | `example/g1/audio/g1_audio_client_example.py`、`example/a2/audio/a2_audio_client_example.py` |
| 避障开关/移动 | `example/obstacles_avoid/obstacles_avoid_switch.py`、`obstacles_avoid_move.py` |
| 无线手柄 | `example/wireless_controller/wireless_controller.py`（需 `pygame`） |

---

## 五、RPC 错误码速查

| 错误码 | 常量名 | 含义 |
| :-- | :-- | :-- |
| 0 | `RPC_OK` | 成功 |
| 3001 | `RPC_ERR_UNKNOWN` | 未知错误 |
| 3102 | `RPC_ERR_CLIENT_SEND` | 客户端发送失败 |
| 3103 | `RPC_ERR_CLIENT_API_NOT_REG` | API 未注册 |
| 3104 | `RPC_ERR_CLIENT_API_TIMEOUT` | 等待响应超时 |
| 3105 | `RPC_ERR_CLIENT_API_NOT_MATCH` | 响应 `api_id` 与请求不匹配 |
| 3106 | `RPC_ERR_CLIENT_API_DATA` | 请求数据错误 |
| 3107 | `RPC_ERR_CLIENT_LEASE_INVALID` | 客户端租约无效 |
| 3201 | `RPC_ERR_SERVER_SEND` | 服务端发送失败 |
| 3202 | `RPC_ERR_SERVER_INTERNAL` | 服务端内部错误 |
| 3203 | `RPC_ERR_SERVER_API_NOT_IMPL` | API 未实现 |
| 3204 | `RPC_ERR_SERVER_API_PARAMETER` | 参数错误 |
| 3205 | `RPC_ERR_SERVER_LEASE_DENIED` | 租约被拒绝 |
| 3206 | `RPC_ERR_SERVER_LEASE_NOT_EXIST` | 租约不存在 |
| 3207 | `RPC_ERR_SERVER_LEASE_EXIST` | 租约已存在 |

常量定义集中在 `unitree_sdk2py/rpc/internal.py`。

---

## 六、已知风险摘要

完整清单（含级别、位置、影响与改造建议）见 [ARCHITECTURE.md](ARCHITECTURE.md) 第八节。最需要注意的几条：

| 级别 | 问题 |
| :-- | :-- |
| P0 | `rpc/client_base.py` 的 `_CallRequestWithParamAndBinNoReply*` 引用未定义变量 `request_binary`，调用即 `NameError` |
| P0 | `idl/default.py` 中 `RequestLease_` / `Response_` 默认构造参数个数与数据类不符，调用即 `TypeError` |
| P1 | `ChannelPublisher.Write(timeout=None)` 不等待订阅者匹配，对端未就绪时静默丢包 |
| P1 | `utils/timerfd.py` 导入即绑定 Linux 符号，Windows/macOS 上 `utils.thread`、`utils.hz_sample` 不可用 |
| P1 | `BQueue.Interrupt` 的 `notify` / `notify_all` 语义与参数名相反 |
| P2 | `pygame` 未声明为依赖；`LogicJoystick.update` 引用不存在的 `self.LS/self.RS` |
| P3 | 仓库无 pytest 用例、无 CI，改造缺少回归保护 |

---

## 七、文档索引

| 文档 | 内容 |
| :-- | :-- |
| [README.md](README.md) | 安装、快速开始、示例索引、错误码、风险摘要 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | 技术栈、分层架构、模块职责、调用关系、机型服务矩阵、线程模型、已知风险、改造边界 |
| [README zh.md](README%20zh.md) | 上游中文版说明（示例路径为旧结构，已不再准确） |
| [AGENTS.md](AGENTS.md) | 遗留改造规范与红线 |
| [init.md](init.md) | 初始化四步准备引导 |

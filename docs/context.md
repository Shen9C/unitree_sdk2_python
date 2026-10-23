# docs/context.md —— 系统现状

> 初始化第 1 项「系统现状」的固化结果。来源：`README.md`、`ARCHITECTURE.md`、`contracts/`。
> 本文件只描述现状，不含改造计划（计划见 [goal.md](goal.md)）。

## 一、代码库

| 项 | 值 |
| :-- | :-- |
| 位置 | `e:\200_Coding\unitree_sdk2_python` |
| 包名 / 版本 | `unitree_sdk2py` / `1.0.1` |
| 许可证 | BSD-3-Clause |
| 上游 | https://github.com/unitreerobotics/unitree_sdk2_python |

## 二、技术栈

- Python >= 3.8（开发环境 3.10）。
- `cyclonedds == 0.10.2`，DDS 总线。
- IDL 生成类：`unitree_go`（20 电机）、`unitree_hg`（35 电机）、`unitree_api`（RPC）。
- `numpy`、`opencv-python`；手柄示例另需 `pygame`（未声明依赖）。
- 打包：setuptools + `pyproject.toml` + `uv.lock`。

## 三、分层与职责

`example/` → `<robot>/<service>/` → `rpc/` → `core/` → `idl/` → `utils/`

| 层 | 职责 |
| :-- | :-- |
| `example/` | 可运行示例，非库代码 |
| `<robot>/<service>/` | 各机型业务客户端（`SportClient` / `LocoClient` / 视频 / 音频 / `robot_state` 等） |
| `rpc/` | RPC 客户端/服务端、租约、Future |
| `core/` | DDS 通道封装与初始化 |
| `idl/` | 生成的 DDS 消息类 |
| `utils/` | CRC、线程、队列、Future、Hz 采样、手柄 |

## 四、现有文档

| 文件 | 内容 |
| :-- | :-- |
| [README.md](file:///e:/200_Coding/unitree_sdk2_python/README.md) | 技术栈、安装、示例索引、错误码与风险摘要 |
| [ARCHITECTURE.md](file:///e:/200_Coding/unitree_sdk2_python/ARCHITECTURE.md) | 分层架构、调用关系、机型矩阵、线程模型、风险 R1–R16 |
| [contracts/README.md](file:///e:/200_Coding/unitree_sdk2_python/contracts/README.md) | 冻结规则、全局契约、错误码、IDL/CRC、缺陷登记 C1–C8 |
| [contracts/python-api.md](file:///e:/200_Coding/unitree_sdk2_python/contracts/python-api.md) | `core` / `rpc` / `utils` 公共 API 契约 |
| [contracts/robot-services.md](file:///e:/200_Coding/unitree_sdk2_python/contracts/robot-services.md) | 机器人服务、DDS topic、事件与定时任务契约 |

## 五、已知痛点

- **无测试、无 CI**（R16）：改造前无安全网，需先补核心路径单测。
- **C1（P0）**：`b2/robot_state/robot_state_client.py` 导入不存在的 `rpc.client_internal`，导入即 `ModuleNotFoundError`。
- **C2/C3（P1）**：音频 `PlayStop()` 恒返回 0；g1 `TtsMaker` 索引自乘，TTS 编号不递增。
- **C5/C6（P2）**：`RecurrentThread` 的 `interval<=0` 分支必抛 `AttributeError`；`ChannelPublisher.Write` 异常兜底分支再抛 `TypeError`。
- **契约陷阱**：g1/h2/r1 服务名为 `sport`、h1 为 `loco`，但类名同为 `LocoClient`；`Move` 的 JSON 键在不同服务下为 `x/y/z` 或 `x/y/yaw`。
- **平台限制**：CRC 加速 `.so` 与 `timerfd` 周期线程仅 Linux；Windows 下 `RecurrentThread` 不可用。
- **租约不可停止**（R10）：`LeaseClient` 守护线程无公开停止接口。

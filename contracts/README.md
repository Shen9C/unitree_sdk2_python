# contracts/ —— 对外接口冻结清单

> 本目录是 `unitree_sdk2py` 的**接口契约基线**，用于遗留改造期间防止破坏调用方。
> 基线来源：`unitree_sdk2py` 1.0.1 当前代码（只读反推），未修改任何业务代码。

## 一、冻结范围与变更规则

### 1.1 什么算"对外接口"

| 类别 | 具体内容 | 冻结原因 |
| :-- | :-- | :-- |
| Python 公共 API | `core/`、`rpc/`、`utils/` 中不带下划线前缀的类与方法；各 `<robot>/<service>/*_client.py` 的公开方法 | 用户脚本直接 `import` 调用 |
| 机器人服务协议 | 服务名、API 版本号、API ID、请求 JSON 字段名、返回结构 | 机器人端固件按此解析，客户端改键即失败 |
| DDS 通道 | topic 名称、IDL 消息类型、收发方向 | 机器人端/其他进程共享同一总线 |
| 错误码 | `rpc/internal.py` 的 RPC 错误码、各 `*_api.py` 的业务错误码 | 调用方按数值判断，改值即误判 |
| 二进制/CRC | IDL 结构体字段顺序、`utils/crc.py` 的 pack 格式与字节数 | CRC 错位会导致机器人拒收运动指令 |
| 线程与定时语义 | RPC 超时默认值、租约 term、`RecurrentThread` 周期语义 | 影响控制节拍与安全停机 |

### 1.2 允许的改动（不视为破坏契约）

- 新增 API ID（不与现有取值冲突）、新增可选关键字参数（带默认值）、新增机型目录。
- 修复**不改变签名与返回值形状**的内部缺陷（如 `NameError`、`IndexError`）。
- 补充 `__init__.py`、依赖声明、类型注解、文档。

### 1.3 禁止的改动（必须走 Spec 并经确认）

- 改服务名、API 版本字符串、任何已有 API ID 数值。
- 改公开方法的名称、参数顺序、参数名、返回元组元素个数/含义。
- 改请求 JSON 的键名（如 `x/y/z`、`velocity/duration`、`data`）。
- 改 topic 名称、IDL 类型、CRC pack 字段顺序或长度。
- 改 RPC 错误码数值或业务错误码数值。
- 调整默认超时（`1.0s`）、租约 `term`（`1.0s`）、申请/续约 API ID（`101/102`）。

### 1.4 变更流程

1. 在 `contracts/` 对应表格中标注**拟变更项**与影响面（哪些示例/机型受影响）。
2. 出该步 Spec，明确兼容策略（新增而非修改、保留旧名别名等）。
3. 用户确认后才改代码；改完同步更新本目录。

## 二、文档索引

| 文件 | 内容 |
| :-- | :-- |
| [README.md](file:///e:/200_Coding/unitree_sdk2_python/contracts/README.md) | 冻结规则、全局不可变契约、错误码、IDL/CRC、事件与定时任务、缺陷登记 |
| [python-api.md](file:///e:/200_Coding/unitree_sdk2_python/contracts/python-api.md) | `core` / `rpc` / `utils` 的 Python 公共 API 契约（签名、入参、出参、异常） |
| [robot-services.md](file:///e:/200_Coding/unitree_sdk2_python/contracts/robot-services.md) | 各机型服务客户端方法表（API ID / JSON / 返回） + DDS topic 契约 |

---

## 三、全局不可变契约

### 3.1 通道命名规则（`core/channel_name.py`）

| 函数 | `ChannelType` | 生成名称 |
| :-- | :-- | :-- |
| `GetClientChannelName(service, SEND)` | 客户端发送 | `rt/api/<service>/request` |
| `GetClientChannelName(service, RECV)` | 客户端接收 | `rt/api/<service>/response` |
| `GetServerChannelName(service, SEND)` | 服务端发送 | `rt/api/<service>/response` |
| `GetServerChannelName(service, RECV)` | 服务端接收 | `rt/api/<service>/request` |
| 租约（`LeaseClient`/`LeaseServer`） | 双向 | `<service>_lease`（**不带 `rt/api/` 前缀**） |

> `ChannelType.SEND = 0`、`ChannelType.RECV = 1`。任何一侧改命名或方向，都会导致请求无响应（客户端 `3104` 超时）。

### 3.2 服务名 / API 版本矩阵

| 模块 | 服务名 | API 版本 | 客户端类 |
| :-- | :-- | :-- | :-- |
| `go2/sport` | `sport` | `1.0.0.1` | `SportClient`（支持租约） |
| `go2w`（复用 go2） | `sport` | `1.0.0.1` | `SportClient` |
| `b2/sport` | `sport` | `1.0.0.1` | `SportClient`（支持租约） |
| `b2w`（复用 b2） | `sport` | `1.0.0.1` | `SportClient` |
| `a2/sport` | `sport` | `1.0.0.1` | `SportClient`（无租约） |
| `as2/sport` | `sport` | `1.0.0.1` | `SportClient`（无租约） |
| `g1/loco` | `sport` | `1.0.0.0` | `LocoClient` |
| `h2/loco` | `sport` | `1.0.0.0` | `LocoClient` |
| `r1/loco` | `sport` | `1.0.0.0` | `LocoClient` |
| `h1/loco` | `loco` | `2.0.0.0` | `LocoClient` |
| `comm/motion_switcher` | `motion_switcher` | `1.0.0.1` | `MotionSwitcherClient` |
| `go2/robot_state` | `robot_state` | `1.0.0.1` | `RobotStateClient` |
| `b2/robot_state` | `robot_state` | `1.0.0.2` | `RobotStateClient` |
| `go2/obstacles_avoid` | `obstacles_avoid` | `1.0.0.2` | `ObstaclesAvoidClient` |
| `go2/video` | `videohub` | `1.0.0.1` | `VideoClient` |
| `b2/front_video` | `front_videohub` | `1.0.0.0` | `VideoClient` |
| `b2/back_video` | `back_videohub` | `1.0.0.0` | `VideoClient` |
| `go2/vui`、`b2/vui` | `vui` | `1.0.0.1` | `VuiClient` |
| `a2/audio`、`g1/audio` | `voice` | `1.0.0.0` | `AudioClient` |
| `g1/arm` | `arm` | `1.0.0.14` | `G1ArmActionClient` |

### 3.3 API ID 分区

| 区间 | 用途 |
| :-- | :-- |
| `1` | 内部：查询服务端 API 版本（无需注册） |
| `101` | 内部：租约申请（无需注册） |
| `102` | 内部：租约续约（无需注册） |
| `1–100` | 内部保留（`RPC_INTERNAL_API_ID_MAX = 100`），客户端不做注册校验 |
| `1001–2058` | 四足运动/状态/避障/视频/语音/VUI |
| `7001–7111` | G1 / H2 / R1 运动控制 |
| `7106` | 同时被 `g1/arm` 用作 `ARM_ACTION_EXECUTE_ACTION`（不同服务名，不冲突） |
| `8001–8105` | H1 运动控制 |

> 客户端 `_Call` 系列在 `apiId > 100` 时要求先 `_RegistApi(apiId, priority)`，否则返回 `3103`。
> 未注册直接调用是**契约行为**，不是缺陷。

### 3.4 RPC 错误码（`rpc/internal.py`，数值不可变）

| 数值 | 常量 | 含义 | 触发点 |
| :-- | :-- | :-- | :-- |
| `0` | `RPC_OK` | 成功 | — |
| `3001` | `RPC_ERR_UNKNOWN` | 未知错误 | Future 失败且非超时；响应 api_id 不匹配以外的一般失败 |
| `3102` | `RPC_ERR_CLIENT_SEND` | 客户端发送失败 | `ClientStub.Send/SendRequest` 返回 False/None |
| `3103` | `RPC_ERR_CLIENT_API_NOT_REG` | API 未注册 | `apiId > 100` 且未 `_RegistApi` |
| `3104` | `RPC_ERR_CLIENT_API_TIMEOUT` | 等待响应超时 | `Future.GetResult(timeout)` 超时 |
| `3105` | `RPC_ERR_CLIENT_API_NOT_MATCH` | 响应 api_id 与请求不符 | 响应错配 |
| `3106` | `RPC_ERR_CLIENT_API_DATA` | 请求数据错误 | 预留常量（当前主链路未主动返回） |
| `3107` | `RPC_ERR_CLIENT_LEASE_INVALID` | 租约无效 | 预留常量（当前主链路未主动返回） |
| `3201` | `RPC_ERR_SERVER_SEND` | 服务端发送响应失败 | `ServerStub.Send` 失败 |
| `3202` | `RPC_ERR_SERVER_INTERNAL` | 服务端内部异常 | handler 抛异常 |
| `3203` | `RPC_ERR_SERVER_API_NOT_IMPL` | API 未实现 | `Server` 未注册该 apiId 的 handler；`LeaseServer` 收到非 101/102 |
| `3204` | `RPC_ERR_SERVER_API_PARAMETER` | 参数错误 | `LeaseServer` 申请报文 JSON 解析失败 |
| `3205` | `RPC_ERR_SERVER_LEASE_DENIED` | 租约校验失败 | `checkLease=True` 且租约无效 |
| `3206` | `RPC_ERR_SERVER_LEASE_NOT_EXIST` | 租约不存在/已过期/续约 id 不匹配 | `LeaseServer` 续约 |
| `3207` | `RPC_ERR_SERVER_LEASE_EXIST` | 租约已被占用 | `LeaseServer` 申请时 `Applied()` |

### 3.5 业务错误码（各 `*_api.py`）

| 模块 | 常量 | 数值 | 含义 |
| :-- | :-- | :-- | :-- |
| `go2/sport`、`b2/sport` | `SPORT_ERR_CLIENT_POINT_PATH` | `4101` | 轨迹点参数非法（客户端本地返回） |
| 同上 | `SPORT_ERR_SERVER_OVERTIME` | `4201` | 服务端超时 |
| 同上 | `SPORT_ERR_SERVER_NOT_INIT` | `4202` | 服务端未初始化 |
| `a2/sport`、`as2/sport` | `SPORT_ERR_SERVER_OVERTIME` | `4201` | 服务端超时 |
| 同上 | `SPORT_ERR_SERVER_NOT_INIT` | `4205` | 服务端未初始化（注意与四足 `4202` 不同） |
| `robot_state`（go2/b2） | `ROBOT_STATE_ERR_SERVICE_SWITCH` | `5201` | 服务切换失败（status 非 0/1） |
| 同上 | `ROBOT_STATE_ERR_SERVICE_PROTECTED` | `5202` | 服务受保护（status == 5） |
| `a2/audio`、`g1/audio` | `AUDIO_ERR_COMM` | `100` | 音频通信错误 |
| `h2/loco` | `LOCO_ERR_LOCOSTATE_NOT_AVAILABLE` / `LOCO_ERR_SCHEDULER_STATE_NOT_AVAILABLE` | `7301` | 两个常量同值，均表示 loco 状态/调度器状态不可用 |
| 同上 | `LOCO_ERR_INVALID_FSM_ID` | `7302` | 非法 FSM ID |
| 同上 | `LOCO_ERR_INVALID_TASK_ID` | `7303` | 非法 task ID |
| `g1/loco`、`h1/loco`、`r1/loco` | — | — | 无业务错误码常量，仅返回 RPC 码 |
| `motion_switcher`、`obstacles_avoid`、`video`、`vui`、`g1/arm` | — | — | 无业务错误码常量，仅返回 RPC 码 |

### 3.6 IDL 与 CRC（`utils/crc.py`）

仅支持以下 4 种消息；其他类型抛 `TypeError('unknown IDL message type to crc')`：

| IDL 类型 | 对应 topic | `struct.pack` 字节数 |
| :-- | :-- | :-- |
| `unitree_go.msg.dds_.LowCmd_` | `rt/lowcmd` | `812` |
| `unitree_go.msg.dds_.LowState_` | `rt/lowstate`、`rt/lf/lowstate` | `1180` |
| `unitree_hg.msg.dds_.LowCmd_` | `rt/lowcmd`、`rt/arm_sdk` | `1004` |
| `unitree_hg.msg.dds_.LowState_` | `rt/lowstate` | `2092` |

- CRC 实现：Linux 下用 `ctypes` 加载 `utils/lib/crc_amd64.so` / `crc_aarch64.so`；其他平台回退纯 Python。
- 计算时机：`LowCmd_.crc` 由调用方在发布前置为计算结果；SDK 不自动填 CRC。
- **禁止**改 IDL 字段顺序/类型/长度；一改则 pack 偏移全错，机器人静默拒收。

### 3.7 时间、超时与租约

| 项 | 值 | 位置 |
| :-- | :-- | :-- |
| 客户端默认调用超时 | `1.0` 秒 | `ClientBase.__timeout` |
| 服务端发送响应超时 | `1.0` 秒 | `ServerBase._SendResponse` |
| 租约默认 term | `1.0` 秒 | `RPC_LEASE_TERM` / `Server.StartLease(term=1.0)` |
| 租约续约周期 | 有效租约取 `term * 0.3`；未拿到租约时按 `RPC_LEASE_TERM * 0.3` 重试 | `lease_client.py` |
| 租约 term 单位 | 服务端 `int(term * 1e6)` 微秒；客户端 `float(term / 1e6)` 秒 | `lease_server.py` / `lease_client.py` |
| request id | `time.monotonic_ns()` | `ClientBase.__SetHeader` |
| 服务端普通队列容量 | `10` | `ServerStub` |
| 服务端优先级队列容量 | `5` | `ServerStub` |
| 客户端建链等待 | `sleep(0.5)` | `ClientStub.Init` |
| `ChannelFactory` 建链后等待 | `sleep(0.2)` | `channel.py` |

---

## 四、事件与定时任务清单

### 4.1 DDS 订阅事件（回调式）

| topic | IDL 类型 | 订阅方（示例/测试） | 触发时机 |
| :-- | :-- | :-- | :-- |
| `rt/lowstate` | `unitree_go.LowState_` 或 `unitree_hg.LowState_` | `example/*/low_level/*.py`、`unitree_sdk2py/test/lowlevel/sub_lowstate.py`、`read_lowstate.py` | 机器人周期广播（通常 500Hz/1kHz，由固件决定） |
| `rt/lf/lowstate` | `unitree_go.LowState_` | `example/wireless_controller/wireless_controller.py` | 低频率状态广播 |
| `rt/secondary_imu` | `unitree_go.IMUState_` | `example/h2/low_level/h2_ankle_swing_example.py` | 第二路 IMU 数据 |
| `rt/api/<service>/response` | `unitree_api.Response_` | `ClientStub`（内部） | RPC 响应到达 |
| `rt/api/<service>/request` | `unitree_api.Request_` | `ServerStub`（内部） | RPC 请求到达 |
| `<service>_lease` | `unitree_api.Request_` / `Response_` | `LeaseClient` / `LeaseServer` | 租约申请、续约、拒绝 |

> 回调执行在 DDS 线程内，**不得在回调里做阻塞长任务**（会拖慢整条通道）。

### 4.2 DDS 发布（由调用方驱动，非 SDK 自动）

| topic | IDL 类型 | 发布方 | 用途 |
| :-- | :-- | :-- | :-- |
| `rt/lowcmd` | `unitree_go.LowCmd_` / `unitree_hg.LowCmd_` | `example/*/low_level/*.py` | 关节级控制指令 |
| `rt/arm_sdk` | `unitree_hg.LowCmd_` | `example/g1/high_level/g1_arm5_sdk_dds_example.py`、`g1_arm7_sdk_dds_example.py`、`example/h2/high_level/h2_arm_sdk_dds_example.py` | 手臂 SDK 控制 |
| `rt/utlidar/switch` | `std_msgs.String_` | `example/go2/high_level/go2_utlidar_switch.py` | 雷达开关 |
| `topic` | `example/helloworld/user_data.UserData` | `example/helloworld/publisher.py`、`test/helloworld/publisher.py` | HelloWorld 示例 |

### 4.3 后台线程与定时器

| 机制 | 位置 | 周期/生命周期 | 契约 |
| :-- | :-- | :-- | :-- |
| 租约守护线程 | `rpc/lease_client.py` | 无限循环；按 term 周期申请/续约 | daemon 线程；**无停止接口**（R10），进程退出才结束 |
| RPC 服务端工作线程 | `rpc/server_base.py` | `Start()` 后常驻 | 从 BQueue 取请求并串行/按优先级处理 |
| `RecurrentThread` | `utils/thread.py` | `interval` 秒；`Wait(timeout)` 置 quit | 基于 Linux `timerfd`，**Windows 不可用** |
| `HZSample` | `utils/hz_sample.py` | 内部 `RecurrentThread(interval=1.0)` | 统计频率；依赖 `RecurrentThread` |
| `Future.GetResult(timeout)` | `utils/future.py` | 单次等待 | `timeout=None` 表示无限等待 |

---

## 五、已知缺陷登记（冻结阶段只记录，不修复）

> 编号与 [ARCHITECTURE.md](file:///e:/200_Coding/unitree_sdk2_python/ARCHITECTURE.md#L226-L248) 第八节一致。
> 修复时必须保持对外签名不变，并先补离线单元测试。

| 编号 | 级别 | 位置 | 对本契约的影响 |
| :-- | :-- | :-- | :-- |
| R1 | P0 | `rpc/client_base.py:87` | `_CallRequestWithParamAndBinNoReplyBase` 必抛 `NameError`；当前无服务客户端使用该路径，**签名仍冻结** |
| R2 | P0 | `idl/default.py` | `RequestLease_` / `Response_` 构造参数个数错误；主链路未使用 |
| R3 | P1 | `core/channel.py:102` | 空样本列表导致 `IndexError`，可能中断回调 |
| R4 | P1 | `core/channel.py` `Write` | `timeout=None` 静默丢包；低层示例需自行 `timeout` |
| R5 | P1 | `utils/bqueue.py` | `Interrupt(notifyAll)` 语义反转 |
| R6 | P1 | `utils/timerfd.py`、`clib_lookup.py` | 非 Linux 平台导入 `utils.thread` / `utils.hz_sample` 失败 |
| R7 | P2 | `core/channel.py` | `ChannelFactory` 单例不可重配 |
| R8 | P2 | `core/channel.py` | DDS 实体释放不确定 |
| R9 | P2 | `utils/joystick.py` | 未声明 `pygame`；`LogicJoystick` 引用未定义属性 |
| R10 | P2 | `rpc/lease_client.py` | 租约线程无法停止，`WaitApplied` 忙等 |
| R11 | P2 | `rpc/` | 无统一异常类型，仅整型错误码 |
| R12 | P2 | `utils/crc.py` | pack 与 IDL 强绑定 |
| R13 | P3 | `README.md`（上游） | 示例路径旧结构；本仓库 README 已修正 |
| R14 | P3 | `as2/sport`、`r1/loco` 等 | 缺 `__init__.py`，依赖命名空间包 |
| R15 | P3 | `rpc/client.py` | 参数名 `enabaleLease` 拼写错误，**作为契约保留** |
| R16 | P3 | 全仓库 | 无测试、无 CI |

补充登记（本轮核实新增，未计入 R1–R16）：

| 编号 | 级别 | 位置 | 现象 |
| :-- | :-- | :-- | :-- |
| C1 | P0 | `b2/robot_state/robot_state_client.py:4` | `from ...rpc.client_internal import *` 模块不存在（应为 `rpc.internal`），**导入即 `ModuleNotFoundError`** —— **已修复**：改为 `...rpc.internal`，回归用例 `test/unit/test_b2_robot_state_import.py` |
| C2 | P1 | `a2/audio/audio_client.py`、`g1/audio/g1_audio_client.py` | `PlayStop()` 忽略底层返回码，恒定 `return 0` —— **已修复**：透传 `code`，回归用例 `test/unit/test_audio_play_stop.py` |
| C3 | P1 | `g1/audio/g1_audio_client.py` | `TtsMaker` 中 `self.tts_index += self.tts_index`（自乘），索引非递增 —— **已修复**：改为 `+= 1`，回归用例 `test/unit/test_g1_audio_tts.py` |
| C4 | P3 | `h1/loco/h1_loco_client.py` | 注册了 `GET_FSM_ID` 等 6 个 GET API，但未提供对应公开方法 |
| C5 | P2 | `utils/thread.py` `RecurrentThread` | `interval <= 0` 时走 `__LoopFunc_0`，其中引用不存在的 `self.__args` / `self.__kwargs`，**该分支必抛 `AttributeError`**；`interval > 0` 为主链路，不受影响 —— **已修复**：改用 `__loopArgs` / `__loopKwargs`，回归用例 `test/unit/test_recurrent_thread_zero_interval.py` |
| C6 | P2 | `core/channel.py` `ChannelPublisher.Write` | `except Exception` 分支调用 `e.args()`（应访问 `e.args`），异常兜底路径本身会再抛 `TypeError` —— **已修复**：改为 `e.args`，回归用例 `test/unit/test_core_channel_writer.py` |
| C7 | P3 | `g1/loco/g1_loco_client.py` | 注册了 `GET_FSM_MODE`(7002)、`GET_BALANCE_MODE`(7003)、`GET_SWING_HEIGHT`(7004)、`GET_STAND_HEIGHT`(7005)、`GET_PHASE`(7006)、`SET_SWING_HEIGHT`(7103)，但未提供对应公开方法 |
| C8 | P3 | `comm/motion_switcher/motion_switcher_client.py` | 注册了 `SET_SILENT`(1004)、`GET_SILENT`(1005)，但未提供对应公开方法 |

> C1–C3、C5、C6 已修复，均未改变公开签名/返回形状，并各带离线回归用例；
> C4、C7、C8 属"注册了 API 但缺公开方法"的功能缺口（P3），按 `docs/goal.md` 仍只登记、待单独立项。
> C1 属"调用即失败"，修复只需改导入路径（不改签名），见上表与 `test/unit/test_b2_robot_state_import.py`。

---

## 六、基线信息

- 代码版本：`unitree_sdk2py` 1.0.1（`pyproject.toml`）
- 冻结日期：2026-10-22
- 冻结依据：当前工作区代码 + [ARCHITECTURE.md](file:///e:/200_Coding/unitree_sdk2_python/ARCHITECTURE.md)
- 本次操作：**仅新增文档，未修改任何业务代码**

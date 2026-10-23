# ARCHITECTURE.md —— unitree_sdk2py 架构说明与风险清单

> 本文档由通读现有代码反向生成（反向文档生成），用于摸清家底、冻结认知。
> 撰写期间**未修改任何源代码**。文中所有结论均可在仓库内对应文件核实。

---

## 一、技术栈

| 类别 | 内容 | 依据 |
| :-- | :-- | :-- |
| 语言 | Python，`requires-python >= 3.8`；开发环境 `.python-version` 为 3.10 | `pyproject.toml` |
| 包名/版本 | `unitree_sdk2py` 1.0.1，许可证 BSD-3-Clause | `pyproject.toml` |
| 通信中间件 | Eclipse CycloneDDS，固定版本 `cyclonedds==0.10.2`（Python binding） | `pyproject.toml` |
| 序列化/数据模型 | 由 IDL 生成的两套 Python 数据类：`unitree_go`（20 电机）与 `unitree_hg`（35 电机），另有 `unitree_api`（RPC 报文） | `unitree_sdk2py/idl/` |
| 数值计算 | `numpy` | `pyproject.toml` |
| 图像 | `opencv-python`（示例取流用） | `pyproject.toml` |
| 手柄 | `pygame`（**未在依赖中声明**） | `unitree_sdk2py/utils/joystick.py` |
| 原生库 | `crc_amd64.so` / `crc_aarch64.so`（CRC 硬件加速，仅 Linux）；Linux `timerfd`（周期线程） | `unitree_sdk2py/utils/crc.py`、`unitree_sdk2py/utils/timerfd.py` |
| 构建/依赖管理 | setuptools（`setup.py` 仅调用 `setup()`，元数据在 `pyproject.toml`）；另有 `uv.lock` 且 `[tool.uv] link-mode = "copy"` | `pyproject.toml`、`setup.py`、`uv.lock` |
| 测试 | **无 pytest / 无自动化测试命令**，`unitree_sdk2py/test/` 全为手工脚本 | 见「六、构建与测试现状」 |

运行平台事实：核心 DDS/RPC 层理论上跨平台，但 `utils/thread.py`、`utils/hz_sample.py` 通过 `utils/timerfd.py` 在**导入时**绑定 Linux `timerfd` 符号，因此这两个模块在 Windows 上不可导入。

---

## 二、目录结构

```
unitree_sdk2_python/
├── unitree_sdk2py/            # SDK 主体（约 201 个 .py，其中大量为生成 IDL）
│   ├── core/                  # DDS 通道层：Channel / ChannelFactory / 通道命名 / QoS 配置
│   ├── rpc/                   # RPC 层：Client/Server 骨架、Future、Lease、错误码
│   ├── idl/                   # DDS 数据模型：unitree_go、unitree_hg、unitree_api 及 default.py
│   ├── utils/                 # 工具：Future、BQueue、Thread/RecurrentThread、CRC、单例、手柄、Hz 统计
│   ├── comm/                  # 跨机型通用服务（motion_switcher）
│   ├── go2/ b2/ b2w/ go2w/    # 四足机型服务客户端（sport/video/robot_state/obstacles_avoid/vui）
│   ├── g1/ h1/ h2/ h1_2/      # 人形机型服务客户端（loco/arm/audio）
│   ├── a2/ as2/ r1/           # 其他机型（sport/loco/audio）
│   └── test/                  # 手工验证脚本（非自动化测试）
├── example/                   # 53 个可运行示例，按机型组织
├── contracts/                 # （尚未创建）第 2 步将冻结的对外接口清单
├── AGENTS.md                  # 遗留改造规范（红线与流程）
├── init.md                    # 初始化引导（四步准备，完成前保留）
├── README.md / README zh.md   # 项目说明
├── pyproject.toml / setup.py  # 打包与依赖
└── uv.lock
```

---

## 三、分层架构

```
┌──────────────────────────────────────────────────────────────┐
│  应用示例层  example/<robot>/<high_level|low_level|camera|...> │
│  仅做参数解析、循环控制、打印；不含协议细节                     │
└───────────────────────────┬──────────────────────────────────┘
                            │ 直接调用服务客户端 / 直接读写 topic
┌───────────────────────────▼──────────────────────────────────┐
│  机器人服务客户端层  unitree_sdk2py/<robot>/<service>/*_client │
│  职责：服务名+API 版本常量、API ID 注册、参数 JSON 约定、返回值  │
└───────────────────────────┬──────────────────────────────────┘
                            │ 继承 Client / 组合 ClientStub
┌───────────────────────────▼──────────────────────────────────┐
│  RPC 层  unitree_sdk2py/rpc/                                   │
│  client.py → client_base.py → client_stub.py                   │
│  server.py → server_base.py → server_stub.py                   │
│  request_future.py / lease_client.py / lease_server.py         │
│  internal.py（内部 API ID、租约期限、错误码）                    │
└───────────────────────────┬──────────────────────────────────┘
                            │ ChannelPublisher / ChannelSubscriber
┌───────────────────────────▼──────────────────────────────────┐
│  DDS 通道层  unitree_sdk2py/core/                              │
│  channel.py（ChannelFactory 单例、Reader/Writer 封装）          │
│  channel_name.py（rt/api/<svc>/request|response）              │
│  channel_config.py（CycloneDDS XML：指定网卡 / 自动选网卡）      │
└───────────────────────────┬──────────────────────────────────┘
                            │ cyclonedds（DDS 实体与 QoS）
┌───────────────────────────▼──────────────────────────────────┐
│  IDL 数据层  unitree_sdk2py/idl/                               │
│  unitree_go（LowCmd/LowState/IMUState…，20 电机）              │
│  unitree_hg（LowCmd_/LowState_…，35 电机）                     │
│  unitree_api（Request/Response/RequestHeader/RequestPolicy…）  │
└──────────────────────────────────────────────────────────────┘
        旁路：utils/（Future、BQueue、Thread、CRC、Singleton、Joystick、HzSample）
```

### 模块职责表

| 模块 | 关键符号 | 职责 | 备注 |
| :-- | :-- | :-- | :-- |
| `core/channel.py` | `ChannelFactory`、`ChannelPublisher`、`ChannelSubscriber`、`ChannelFactoryInitialize` | 管理 DomainParticipant、创建/缓存 Topic、收发样本回调 | 单例；初始化后不可重配 |
| `core/channel_name.py` | `ChannelType`、`GetClientChannelName`、`GetServerChannelName` | RPC topic 命名规则 | 客户端/服务端方向互为镜像 |
| `core/channel_config.py` | 两段 CycloneDDS XML 模板 | 指定网卡或自动选网卡；日志写 `/tmp/cdds.LOG` | 指定网卡分支写死 Linux 路径 |
| `rpc/client.py` | `Client`、`_RegistApi`、`_Call*` | API 注册与调用入口，可选租约 | 构造参数名为 `enabaleLease`（拼写错误已是公共签名） |
| `rpc/client_base.py` | `_CallBase` 系列、错误映射 | 构造 Request、发请求、等 Future、校验 `api_id` | 默认超时 1.0s |
| `rpc/client_stub.py` | `ClientStub` | 建 send/recv 通道，登记 Future，响应回来唤醒 | `Init()` 内 `sleep(0.5)` |
| `rpc/request_future.py` | `RequestFuture`、`RequestFutureQueue` | requestId → Future 映射 | Lock 保护，Get 即 pop |
| `rpc/server.py` / `server_base.py` / `server_stub.py` | `Server`、`_RegistHandler`、`_Start` | 服务端骨架：注册 handler、消费请求队列、可选优先级队列 | `Init()` 为空实现 |
| `rpc/lease_client.py` | `LeaseClient` | 后台线程周期性申请/续约 | `while True`，无退出路径 |
| `rpc/lease_server.py` | 单租约缓存 + 过期判断 | 服务端租约校验 | 仅缓存一个租约 |
| `rpc/internal.py` | `RPC_INTERNAL_API_ID_MAX=100`、`RPC_LEASE_TERM=1.0`、错误码 | 内部协议常量 | API 1/101/102 为内部保留 |
| `idl/default.py` | `unitree_api_msg_dds__*` 默认构造 | 生成 IDL 的默认值封装 | **存在构造参数个数错误**，见风险 R3 |
| `utils/future.py` | `Future`、`FutureState` | 简版异步结果 | DEFER/READY/FAILED |
| `utils/bqueue.py` | `BQueue` | 有界阻塞队列，`Put(replace=True)` 可覆盖最旧 | `Interrupt` 语义反转，见 R5 |
| `utils/thread.py` | `Thread`、`RecurrentThread` | 周期线程，基于 Linux `timerfd` | 非 Linux 不可用 |
| `utils/crc.py` | 4 种 pack 格式 + `.so`/纯 Python 双实现 | 低层控制报文 CRC | 格式与结构体大小强耦合 |
| `utils/singleton.py` | `Singleton` | 线程安全单例基类 | 被 `ChannelFactory` 使用 |
| `utils/joystick.py` | `Joystick`、`LogicJoystick` | pygame 手柄读取与逻辑映射 | 依赖未声明，`update` 有缺陷（R9） |
| `utils/hz_sample.py` | `HzSample` | 统计回调频率 | 依赖 timerfd 线程 |
| `comm/motion_switcher/` | `MotionSwitcherClient` | 切换 ai/normal/advanced 等运控模式 | 与低层控制互斥的常见前置步骤 |

---

## 四、调用关系

### 4.1 高层控制（以 Go2 sport 为例）

```
example/go2/high_level/go2_sport_client.py
  └─ ChannelFactoryInitialize(0, iface)              # core/channel.py
  └─ SportClient()                                    # go2/sport/sport_client.py
       └─ Init(): _RegistApi(1001..2058)              # rpc/client.py
  └─ client.Move(0.3, 0, 0)
       └─ Client._Call(apiId=1008, {"x":..,"y":..,"z":..})
            └─ ClientBase._CallBase
                 ├─ Request(RequestHeader(RequestIdentity(ns, apiId), leaseId),
                 │          RequestPolicy(priority, noReply))
                 ├─ ClientStub.SendRequest → ChannelPublisher.Write("rt/api/sport/request")
                 ├─ RequestFutureQueue.Put(requestId, future)
                 └─ future.GetResult(1.0s)
       ← 响应经 ChannelSubscriber("rt/api/sport/response") 回调
            └─ ClientStub.__OnResponse → queue.Get(requestId).Ready(response)
```

要点：
- 请求 topic：`rt/api/<serviceName>/request`；响应 topic：`rt/api/<serviceName>/response`（见 `core/channel_name.py`）。
- `Move`、`TrajectoryFollow` 使用 `_CallNoReply`（不等待响应），其余 API 走 `_Call`。
- 参数统一为 JSON 字符串：`{"x","y","z"}` 或 `{"data": ...}`；binary 接口（如视频帧）走 `_CallBinary`。

### 4.2 低层控制（以 H1 为例）

```
example/h1/low_level/h1_low_level_example.py
  ├─ ChannelSubscriber("rt/lowstate").Init(handler, 10)   # 状态订阅
  ├─ ChannelPublisher("rt/lowcmd").Init()                 # 指令发布
  ├─ MotionSwitcherClient().CheckMode()/ReleaseMode()      # 先退出运控模式
  ├─ RecurrentThread(interval=0.002, target=...)          # 500Hz 控制循环（Linux）
  └─ loop:
       ├─ 读 LowState（电机 q/dq/tau、IMU）
       ├─ 计算 PD → 填 LowCmd（mode/q/dq/Kp/Kd/tau）
       ├─ crc32(LowCmd) 写入 crc 字段
       └─ publisher.Write(low_cmd)
```

要点：
- 低层指令/状态 topic 因机型而异：四足 `rt/lowcmd`/`rt/lowstate`，G1/H1 另有 `rt/arm_sdk`、`rt/lf/lowstate` 等。
- CRC 结构体格式与 IDL 版本绑定：LowCmd 812B、LowState 1180B、HGLowCmd 1004B、HGLowState 2092B（`utils/crc.py`）。
- 低层示例依赖 `RecurrentThread` → `timerfd`，**只能在 Linux 机器人端运行**。

### 4.3 租约（Lease）时序

```
Client(enabaleLease=True)
  └─ LeaseClient(serviceName, term=1.0)
       └─ daemon thread: while True
            ├─ ApplyLease  → API 101 → <svc>_lease
            ├─ 等待 term*0.3
            └─ Renewal     → API 102
Server(enableLease)
  └─ StartLease(term) → LeaseServer 缓存单租约，逐请求校验过期
```

风险：租约线程无退出条件；`WaitApplied` 为忙等；服务端仅维护一个租约槽位。

---

## 五、机型与服务矩阵

| 机型目录 | 服务客户端 | 服务名 | API 版本 | 依赖 IDL |
| :-- | :-- | :-- | :-- | :-- |
| `go2/` | `sport`、`video`、`robot_state`、`obstacles_avoid`、`vui` | `sport` / `videohub` / `robot_state` / `obstacles_avoid` / `vui` | 1.0.0.1（video 1.0.0.1、robot_state 1.0.0.1、obstacles_avoid 1.0.0.2） | `unitree_go` |
| `b2/` | `sport`、`front_video`、`back_video`、`robot_state`、`vui` | `sport` / `front_videohub` / `back_videohub` / `robot_state` / `vui` | 1.0.0.1（robot_state 1.0.0.2；video 1.0.0.0） | `unitree_go` |
| `b2w/` | 复用 `b2.*` | 同 b2 | 同 b2 | `unitree_go` |
| `go2w/` | 复用 `go2.sport`、`go2.robot_state` | 同 go2 | 同 go2 | `unitree_go` |
| `a2/` | `sport`、`audio` | `sport`（常量名 `ROBOT_SPORT_*`）/ `voice` | sport 1.0.0.1 / voice 1.0.0.0 | `unitree_go` |
| `as2/` | `sport` | `sport` | 1.0.0.1 | `unitree_go` |
| `g1/` | `loco`、`arm`、`audio` | `sport` / `arm` / `voice` | loco 1.0.0.0 / arm 1.0.0.14 / voice 1.0.0.0 | `unitree_hg` |
| `h1/` | `loco` | `loco` | 2.0.0.0 | `unitree_hg` |
| `h1_2/` | 复用 `h1.loco` | `loco` | 2.0.0.0 | `unitree_hg` |
| `h2/` | `loco` | `sport` | 1.0.0.0 | `unitree_hg` |
| `r1/` | `loco` | `sport` | 1.0.0.0 | `unitree_hg` |
| `comm/` | `motion_switcher` | `motion_switcher` | 1.0.0.1 | `unitree_api` |

注意：`as2/sport`、`r1/loco` 等子目录没有 `__init__.py`，以命名空间包形式工作；打包/静态检查时易被忽略。

---

## 六、构建与测试现状

- 安装：`pip install -e .`（依赖 `cyclonedds==0.10.2`，需可用的 `CYCLONEDDS_HOME`）。
- 构建：setuptools 默认流程，无自定义 build 步骤，无 lint/format 配置。
- 测试：
  - `unitree_sdk2py/test/crc/test_crc.py` 仅打印 CRC 值；
  - `unitree_sdk2py/test/rpc/*` 需真实 DDS 环境与对端服务；
  - **仓库内无 pytest 用例、无 CI 配置、无统一测试入口**。
  - 结论：当前不具备「改前先跑测试」的安全网，补测是改造前置工作。

---

## 七、线程与异步模型

| 机制 | 位置 | 行为 |
| :-- | :-- | :-- |
| `Future` | `utils/future.py` | 三态状态机 + `Condition` 等待；`SetResult` 后唤醒 |
| `RequestFutureQueue` | `rpc/request_future.py` | dict + Lock，按 requestId 取回 |
| `BQueue` | `utils/bqueue.py` | 有界队列，满时按 `replace` 决定阻塞或覆盖 |
| RPC 接收线程 | `rpc/client_stub.py` | DDS 回调内直接入队 + `Ready`，无独立线程 |
| 服务端消费线程 | `rpc/server_stub.py` | 两个 `while True` 线程（普通队列 + 优先级队列） |
| `RecurrentThread` | `utils/thread.py` | Linux timerfd + `os.read` 定时；`Wait()` 仅置标记，下一次 tick 才退出 |
| `LeaseClient` 线程 | `rpc/lease_client.py` | daemon `while True`，无退出条件 |

---

## 八、已知风险

> 分级：**P0** = 调用即失败；**P1** = 特定场景丢包/异常；**P2** = 可维护性/可移植性问题；**P3** = 文档与一致性问题。
> 本次仅记录，不修复。

| 编号 | 级别 | 位置 | 现象 | 影响 |
| :-- | :-- | :-- | :-- | :-- |
| R1 | P0 | `rpc/client_base.py` | `_CallRequestWithParamAndBinNoReply*` 中使用了未定义变量 `request_binary`（形参为 `requestBinary`） | 调用该路径必抛 `NameError` |
| R2 | P0 | `idl/default.py` | `unitree_api_msg_dds__RequestLease_()` 传 3 个参数、`unitree_api_msg_dds__Response_()` 传 6 个参数，与数据类字段数不符 | 一旦调用即 `TypeError`；当前主链路未触发 |
| R3 | P1 | `core/channel.py` | `Channel.__Reader.__OnDataAvailable` 只判 `samples is None`，未判空列表 | 空样本时 `samples[0]` 抛 `IndexError`，可能打断 DDS 回调 |
| R4 | P1 | `core/channel.py` | `__Writer.Write(timeout=None)` 不等待订阅者匹配即写入 | 对端未就绪时**静默丢包** |
| R5 | P1 | `utils/bqueue.py` | `Interrupt(notifyAll=True)` 只 `notify()`，`False` 反而 `notify_all()` | 唤醒语义与命名相反，易导致漏唤醒或多唤醒 |
| R6 | P1 | `utils/timerfd.py`、`utils/clib_lookup.py` | 模块导入即 `CDLL(None)` 查找 Linux 符号 | Windows/macOS 上 `utils.thread`、`utils.hz_sample` 导入失败；低层示例不可跨平台 |
| R7 | P2 | `core/channel.py` | `ChannelFactory` 单例初始化后不可重配；`Init` 创建了 `Domain(id, config)` 但 `DomainParticipant(id)` 只用 id | 多网卡/多域场景行为不直观，误用后需重启进程 |
| R8 | P2 | `core/channel.py` | 关闭用 `del self.__reader`，未显式 `close()/delete()` DDS 实体；创建后有 `sleep(0.2)`、`sleep(0.5)` | 资源释放不确定；启动固定延迟 |
| R9 | P2 | `utils/joystick.py` | 依赖 `pygame` 但未在依赖中声明；`LogicJoystick.update` 引用不存在的 `self.LS/self.RS` | 新环境导入失败；逻辑摇杆路径运行时报 `AttributeError` |
| R10 | P2 | `rpc/lease_client.py` | 后台线程 `while True` 无退出；`WaitApplied` 忙等 | 无法优雅关闭；CPU 空转 |
| R11 | P2 | `rpc/` 全层 | 错误码以整型常量散落在 `internal.py` 与各 `*_base.py`，无统一异常类型 | 调用方只能比较数字，错误处理易遗漏 |
| R12 | P2 | `utils/crc.py` | 结构体 pack 格式与 IDL 字段强绑定（812/1180/1004/2092 字节） | IDL 或字段一旦变化，CRC 静默错位，机器人拒收指令 |
| R13 | P3 | `README.md`、`README zh.md` | 示例路径为旧结构（如 `example/high_level/...`、`example/front_camera/...`） | 照文档执行会 `FileNotFoundError`；已在本仓库版 README 中修正 |
| R14 | P3 | `as2/sport`、`r1/loco` 等目录 | 缺 `__init__.py`，以命名空间包工作 | 打包配置、IDE 索引、静态分析可能漏掉 |
| R15 | P3 | `rpc/client.py` | 公共参数名 `enabaleLease` 拼写错误 | 只能按位置传参或写错关键字；改名会破坏兼容，需冻结 |
| R16 | P3 | 全仓库 | 无自动化测试、无 CI | 任何改造缺少回归保护 |

---

## 九、改造边界建议（供第 2 步冻结接口时参考）

1. **优先冻结**：`ChannelFactoryInitialize`、`ChannelPublisher/ChannelSubscriber` 的公开方法签名、各 `*Client` 的构造与公开方法、`MotionSwitcherClient` 三方法、`Future` 公开方法、RPC 错误码取值。
2. **不可轻动**：IDL 生成目录、CRC pack 格式、topic 命名规则、API ID 与版本常量——这些是机器人端协议契约。
3. **可安全收敛**：R1/R2 这类明确的本地缺陷（需先补可离线运行的单元测试）、`__init__.py` 补全、依赖声明补 `pygame`。
4. **需平台隔离**：`utils/thread.py`、`utils/timerfd.py` 的导入期副作用，应在补测后做延迟绑定，但不改变对外行为。
5. **文档同步**：README 已按当前 `example/<robot>/...` 结构重写；后续改动示例路径须同步本文档矩阵。

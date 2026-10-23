# Python 公共 API 契约（core / rpc / utils）

> 冻结对象：模块中**不带下划线前缀**的类、方法与模块级函数。
> 标注为「内部」的条目仅由 SDK 内部调用，但签名仍受保护，避免二次开发代码依赖后被无意破坏。
> 所有路径均相对 `unitree_sdk2py/`。

## 0. 通用约定

| 项 | 约定 |
| :-- | :-- |
| 返回值风格 | 成对返回 `(code, data)`；`code == 0` 成功，非 0 见 [README.md 3.4](file:///e:/200_Coding/unitree_sdk2_python/contracts/README.md) |
| 无返回调用 | 仅返回 `code`（如 `_CallNoReply`、`Send`） |
| 异常 | 仅 `ChannelFactoryInitialize` 主动抛 `Exception`；`CRC.Crc` 抛 `TypeError`；其余内部捕获后返回错误码/`None` |
| 超时单位 | 秒（`float`） |
| 线程安全 | `BQueue`、`RequestFutureQueue`、`LeaseContext` 自带锁；`Channel` 本身不加锁 |
| 初始化顺序 | 必须先 `ChannelFactoryInitialize(...)`，再构造任何 `*Client` / `ChannelPublisher` / `ChannelSubscriber` |

---

## 1. `core/channel.py`

### 1.1 `ChannelFactoryInitialize(id: int = 0, networkInterface: str = None) -> None`

| 项 | 内容 |
| :-- | :-- |
| 调用方 | 所有示例脚本入口（如 `example/go2/high_level/go2_sport_client.py`）、`unitree_sdk2py/test/**` |
| 入参 | `id`：DDS Domain ID，默认 `0`；`networkInterface`：网卡名，`None` 表示自动选择 |
| 出参 | 无 |
| 异常 | 初始化失败抛 `Exception("channel factory init error.")` |
| 副作用 | 创建全局 `Domain` + `DomainParticipant`；**进程内只生效一次**（单例幂等） |

### 1.2 `ChannelFactory`（单例，内部）

| 方法 | 入参 | 出参 | 说明 |
| :-- | :-- | :-- | :-- |
| `Init(id, networkInterface=None, qos=None)` | 同上 | `bool` | 已初始化直接返回 `True`；失败返回 `False`，不抛异常 |
| `CreateChannel(name, type)` | topic 名、IDL 类型 | `Channel` | 未初始化时 `participant` 为 `None`，后续使用会失败 |
| `CreateSendChannel(name, type)` | 同上 | `Channel` | 等价 `CreateChannel` + `SetWriter(None)` |
| `CreateRecvChannel(name, type, handler=None, queueLen=0)` | 同上 + 回调、队列长度 | `Channel` | `queueLen > 0` 时回调在独立线程串行执行；`0` 时在 DDS 线程执行 |

### 1.3 `ChannelPublisher`

| 方法 | 入参 | 出参 | 调用方 |
| :-- | :-- | :-- | :-- |
| `__init__(name: str, type: Any)` | topic 名、IDL 类型 | — | `example/helloworld/publisher.py`、低层示例、`h2_ankle_swing_example.py` |
| `Init() -> None` | — | — | 同上；幂等 |
| `Write(sample: Any, timeout: float = None) -> bool` | IDL 消息、等待匹配超时 | `True` 写入成功；`False` 未匹配/写失败 | 控制循环 |
| `Close() -> None` | — | — | 释放 writer |

**`Write` 语义（冻结）**：
- `timeout=None`：不等待订阅者匹配，**直接写**，无订阅者时静默丢弃（R4）。
- `timeout>0`：最多等待 `timeout` 秒直到 `publication_matched`；仍未匹配返回 `False`。
- 捕获 `DDSException` 返回 `False`，不抛出。

### 1.4 `ChannelSubscriber`

| 方法 | 入参 | 出参 | 调用方 |
| :-- | :-- | :-- | :-- |
| `__init__(name: str, type: Any)` | topic 名、IDL 类型 | — | 低层状态订阅示例、`sub_lowstate.py` |
| `Init(handler: Callable = None, queueLen: int = 0) -> None` | 回调、队列长度 | — | 同上；幂等 |
| `Read(timeout: int = None) -> Any` | 秒 | IDL 样本或 `None`（超时/异常） | 主动读取模式（不使用 handler 时） |
| `Close() -> None` | — | — | 释放 reader，停止读线程 |

**回调契约**：
- `handler(sample)` 在 SDK 线程中调用；`queueLen=0` 时为 DDS 线程，`>0` 时为 `ch_reader` 线程。
- handler 抛异常不会被吞掉（`queueLen=0` 路径），会冒泡到 DDS 回调层。
- `queueLen>0` 时队列满默认丢弃最旧样本（`BQueue.Put(sample)` 无 `replace`，实际**丢弃新样本**）。

### 1.5 `Channel`（内部）

| 方法 | 出参 | 说明 |
| :-- | :-- | :-- |
| `SetWriter(qos=None)` / `SetReader(qos=None, handler=None, queueLen=0)` | — | 初始化读写端 |
| `Write(sample, timeout=None)` | `bool` | 转发 `__Writer.Write` |
| `Read(timeout=None)` | 样本/`None` | 转发 `__Reader.Read` |
| `CloseReader()` / `CloseWriter()` | — | 释放 DDS 实体 |

---

## 2. `core/channel_name.py`

| 符号 | 值/签名 | 调用方 |
| :-- | :-- | :-- |
| `ChannelType` | `SEND = 0`、`RECV = 1` | `ClientStub`、`ServerStub` |
| `GetClientChannelName(serviceName: str, channelType: ChannelType) -> str` | `SEND`→`rt/api/<s>/request`；`RECV`→`rt/api/<s>/response` | `ClientStub.Init` |
| `GetServerChannelName(serviceName: str, channelType: ChannelType) -> str` | `SEND`→`rt/api/<s>/response`；`RECV`→`rt/api/<s>/request` | `ServerStub.Init` |

---

## 3. `rpc/client_base.py` —— `ClientBase`

构造：`ClientBase(serviceName: str)`（内部 `ClientStub.Init()` + `sleep(0.5)`）。

| 方法 | 入参 | 出参 | 说明 |
| :-- | :-- | :-- | :-- |
| `SetTimeout(timeout: float)` | 秒 | — | 改默认 `1.0s`；影响发送与等待响应 |
| `_CallBase(apiId, parameter: str, proirity=0, leaseId=0)` | apiId、JSON 字符串、优先级、租约 id | `(code, data: str)` | 同步请求-响应；code 见 3.4 |
| `_CallNoReplyBase(apiId, parameter, proirity, leaseId)` | 同上 | `code` | 不等待响应 |
| `_CallRequestWithParamAndBinBase(apiId, requestParamter, requestBinary, proirity=0, leaseId=0)` | JSON + 二进制 list | `(code, data)` | 音频流等 |
| `_CallRequestWithParamAndBinNoReplyBase(...)` | 同上 | `code` | **R1：必抛 `NameError`**，当前无调用方 |
| `_CallBinaryBase(apiId, parameter: list, proirity, leaseId)` | 二进制 list | `(code, binary: list)` | 视频帧等 |
| `_CallBinaryNoReplyBase(apiId, parameter, proirity, leaseId)` | 同上 | `code` | 不等待响应 |

**错误码映射（冻结）**：

| 场景 | 返回 |
| :-- | :-- |
| `SendRequest` 返回 `None` | `(3102, None)` / `3102` |
| Future 超时 | `(3104, None)` |
| Future 其他失败 | `(3001, None)` |
| 响应 `api_id` 不匹配 | `(3105, None)` |
| 正常 | `(response.status.code, response.data/binary)` |

> `parameter` 必须是 **JSON 字符串**（`json.dumps(dict)`）；空参数用 `"{}"`。

---

## 4. `rpc/client.py` —— `Client(ClientBase)`

### 4.1 构造与生命周期

| 成员 | 签名 | 说明 |
| :-- | :-- | :-- |
| `__init__` | `Client(serviceName: str, enabaleLease: bool = False)` | **参数名拼写 `enabaleLease` 冻结**（R15）；`True` 时立即创建 `LeaseClient` 并启动后台线程 |
| `WaitLeaseApplied()` | `-> None` | 忙等直至拿到租约；未启用租约时立即返回 |
| `GetLeaseId()` | `-> int \| None` | 未启用返回 `None` |
| `GetApiVersion()` | `-> str \| None` | 本端声明的版本（`_SetApiVersion` 设置） |
| `GetServerApiVersion()` | `-> (code, str \| None)` | 调内部 apiId `1` 查询服务端版本 |
| `_SetApiVersion(apiVersion: str)` | — | 子类 `Init()` 调用 |

### 4.2 调用方法（子类使用）

| 方法 | 入参 | 出参 | 校验 |
| :-- | :-- | :-- | :-- |
| `_Call(apiId, parameter)` | apiId、JSON | `(code, data)` | `apiId>100` 未注册→`(3103, None)` |
| `_CallNoReply(apiId, parameter)` | 同上 | `code` | 同上→`3103` |
| `_CallRequestWithParamAndBin(apiId, requestParamter, requestBinary)` | JSON + list | `(code, data)` | 同上→`(3103, None)` |
| `_CallRequestWithParamAndBinNoReply(...)` | 同上 | `code` | 同上→`3103`；底层命中 R1 |
| `_CallBinary(apiId, parameter: list)` | list | `(code, binary)` | 同上→`(3103, None)` |
| `_CallBinaryNoReply(apiId, parameter)` | list | `code` | 同上→`3103` |
| `_RegistApi(apiId: int, proirity: int)` | apiId、优先级 | — | `proirity>0` 走服务端优先级队列 |

---

## 5. `rpc/client_stub.py` —— `ClientStub`（内部）

| 方法 | 入参 | 出参 | 说明 |
| :-- | :-- | :-- | :-- |
| `__init__(serviceName)` | — | — | 不建链 |
| `Init()` | — | — | 建 send/recv 通道，recv 回调队列长度 `10`，`sleep(0.5)` |
| `Send(request: Request, timeout: float)` | 请求、超时 | `bool` | 无 future |
| `SendRequest(request, timeout)` | 同上 | `RequestFuture \| None` | 先登记 future 再发送；失败移除并返回 `None` |
| `RemoveFuture(requestId: int)` | — | — | 超时清理 |

---

## 6. `rpc/server.py` —— `Server(ServerBase)`

| 方法 | 签名 | 说明 |
| :-- | :-- | :-- |
| `__init__` | `Server(name: str)` | 服务名即通道名主体 |
| `Init()` | `-> None` | **空实现**（保留兼容） |
| `StartLease(term: float = 1.0)` | — | 启用租约；创建 `<name>_lease` 服务端 |
| `Start(enablePrioQueue: bool = False)` | — | 建链并启动工作线程 |
| `GetApiVersion()` / `_SetApiVersion(str)` | — | 服务版本（apiId `1` 返回） |
| `_RegistHandler(apiId, handler, checkLease)` | handler：`parameter(str) -> (code, data)` | 注册普通 API |
| `_RegistBinaryHandler(apiId, handler, checkLease)` | handler：`binary(list) -> (code, list)` | 注册二进制 API |

**处理语义（冻结）**：

1. `apiId == 1`：返回 `__apiVersion`，无需注册。
2. 未注册 handler：`3203`。
3. `checkLease=True` 且租约校验失败：`3205`，不调用 handler。
4. handler 正常：采用其 `(code, data)`；`code != 0` 时 `data` 置空。
5. handler 抛任何异常：`3202`（异常被完全吞掉，不打印）。
6. `policy.noreply == True`：**不发响应**。

---

## 7. `rpc/server_base.py` —— `ServerBase`

| 方法 | 签名 | 说明 |
| :-- | :-- | :-- |
| `GetName()` | `-> str` | 服务名 |
| `_Start(enablePrioQueue=False)` | — | 委托 `ServerStub.Init` + `sleep(0.5)` |
| `_SetServerRequestHandler(handler)` | `Callable[[Request], None]` | 注入请求处理函数 |
| `_SendResponse(response)` | — | 发送超时 `1.0s`，失败仅打印 |

---

## 8. `rpc/server_stub.py` —— `ServerStub`（内部）

| 方法 | 签名 | 说明 |
| :-- | :-- | :-- |
| `Init(serverRequestHander, enablePriority=False)` | — | 普通队列 `BQueue(10)`；优先级队列 `BQueue(5)`；各起一个 daemon 线程 |
| `Send(response, timeout)` | `-> bool` | 发送响应 |

**分流规则**：`enablePriority=True` 且 `request.header.policy.priority > 0` → 优先级队列，否则普通队列。
队列满时 `Put(request, True)` 覆盖最旧请求。

---

## 9. `rpc/lease_client.py` —— `LeaseClient(ClientBase)`

| 成员 | 签名 | 说明 |
| :-- | :-- | :-- |
| `__init__` | `LeaseClient(name: str)` | 通道名 `<name>_lease`；contextName `hostname/name/pid` |
| `Init()` | — | `SetTimeout(1.0)` + 启动 daemon 线程（无限循环，R10） |
| `WaitApplied()` | — | 忙等，`sleep(0.1)`；**无超时** |
| `GetId()` | `-> int` | `0` 表示未持有 |
| `Applied()` | `-> bool` | `id != 0` |

**协议**：
- 申请：`_CallBase(101, {"name": contextName})` → 成功返回 `{"id": int, "term": 微秒}`。
- 续约：`_CallBase(102, "{}", 0, leaseId)`；返回 `3206` 时本地 `Reset()`。
- 等待间隔：持有租约 `term*0.3`，未持有 `1.0*0.3` 秒。

---

## 10. `rpc/lease_server.py` —— `LeaseServer(ServerBase)`

| 成员 | 签名 | 说明 |
| :-- | :-- | :-- |
| `__init__` | `LeaseServer(name: str, term: float)` | 通道名 `<name>_lease`；`term` 转微秒整数 |
| `Init()` | — | 空实现 |
| `Start(enablePrioQueue=False)` | — | 启动 |
| `CheckRequestLeaseDenied(leaseId) -> bool` | — | 无租约/过期/不匹配返回 `True`；过期时 `Clear()` 后返回 `False` |

**响应契约**：

| 请求 | 条件 | code | data |
| :-- | :-- | :-- | :-- |
| 101 申请 | 无租约或已过期 | `0` | `{"id": now_us, "term": term_us}` |
| 101 申请 | 他人持有且未过期 | `3207` | `""` |
| 101 申请 | JSON 解析失败 | `3204` | `""` |
| 102 续约 | id 匹配且未过期 | `0` | `""` |
| 102 续约 | id 不匹配或已过期 | `3206` | `""` |
| 其他 apiId | — | `3203` | `""` |

---

## 11. `rpc/request_future.py`

| 类/方法 | 签名 | 说明 |
| :-- | :-- | :-- |
| `RequestFuture` | `(Future)` | RPC 响应 future |
| `SetRequestId(id)` / `GetRequestId()` | — | 关联请求 id |
| `RequestFutureQueue.Set(id, future) -> bool` | — | future 为 `None` 返回 `False` |
| `RequestFutureQueue.Get(id)` | `-> RequestFuture \| None` | **取出即删除** |
| `RequestFutureQueue.Remove(id)` | — | 幂等 |

---

## 12. `rpc/internal.py`（常量，禁止改值）

| 常量 | 值 |
| :-- | :-- |
| `RPC_INTERNAL_API_ID_MAX` | `100` |
| `RPC_API_ID_INTERNAL_API_VERSION` | `1` |
| `RPC_API_ID_LEASE_APPLY` | `101` |
| `RPC_API_ID_LEASE_RENEWAL` | `102` |
| `RPC_LEASE_TERM` | `1.0` |
| 错误码 | 见 [README.md 3.4](file:///e:/200_Coding/unitree_sdk2_python/contracts/README.md) |

---

## 13. `utils/future.py`

| 符号 | 签名/值 | 说明 |
| :-- | :-- | :-- |
| `FutureState` | `DEFER=0`、`READY=1`、`FAILED=2` | 内部状态 |
| `FutureResult.FUTURE_SUCC` | `0` | 成功 |
| `FutureResult.FUTUTE_ERR_TIMEOUT` | `1` | 超时（常量名拼写错误，**冻结**） |
| `FutureResult.FUTURE_ERR_FAILED` | `2` | 已失败 |
| `FutureResult.FUTURE_ERR_UNKNOWN` | `3` | 未知状态 |
| `FutureResult(code, msg, value=None)` | — | `code/msg/value` 公开字段 |
| `Future.GetResult(timeout=None)` | `-> FutureResult` | 超时返回 `code=1` |
| `Future.Wait(timeout=None)` | `-> bool` | 被唤醒返回 `True` |
| `Future.Ready(value)` | `-> bool` | 非 DEFER 状态返回 `False` |
| `Future.Fail(reason: str)` | `-> bool` | 非 DEFER 状态返回 `False` |

---

## 14. `utils/bqueue.py` —— `BQueue`

| 方法 | 签名 | 行为 |
| :-- | :-- | :-- |
| `__init__(maxLen=10)` | — | 有界 FIFO |
| `Put(x, replace=False)` | `-> bool` | 队列满且 `replace=False` 返回 `False`（丢弃新元素）；`True` 覆盖最旧并返回 `False`；未满返回 `True` |
| `Get(timeout=None)` | `-> Any \| None` | 空队列等待；超时/异常返回 `None` |
| `Clear()` | — | 清空 |
| `Size()` | `-> int` | 当前长度 |
| `Interrupt(notifyAll=False)` | — | **R5：语义反转**（`True` 只唤醒一个，`False` 唤醒全部） |

---

## 15. `utils/thread.py`

| 类/方法 | 签名 | 说明 |
| :-- | :-- | :-- |
| `Thread(target=None, name=None, args=(), kwargs=None)` | 继承 `Future` | daemon 线程；结束 `Ready(return)`，异常 `Fail(msg)` |
| `Thread.Start()` | — | 启动 |
| `Thread.GetId()` / `GetNativeId()` | — | 线程标识 |
| `RecurrentThread(interval=1.0, target=None, name=None, args=(), kwargs=None)` | — | 周期执行 |
| `RecurrentThread.Wait(timeout=None)` | — | 置 quit 并等待线程结束 |
| 平台约束 | — | `interval > 0` 时依赖 Linux `timerfd`，**Windows 导入即失败**（R6）；`interval<=0` 分支存在 C5 缺陷 |

---

## 16. `utils/crc.py` —— `CRC(Singleton)`

| 方法 | 签名 | 说明 |
| :-- | :-- | :-- |
| `Crc(msg: idl.IdlStruct) -> int` | 仅接受 4 种 LowCmd/LowState | 其他类型抛 `TypeError('unknown IDL message type to crc')` |

- Linux x86_64/aarch64 走 `.so`；其他平台走纯 Python `_crc_py`。
- 只支持 `unitree_go` / `unitree_hg` 的 `LowCmd_`、`LowState_`。

---

## 17. `utils/singleton.py` —— `Singleton`

| 方法 | 说明 |
| :-- | :-- |
| `__new__(cls)` | 同进程内返回唯一实例；子类共用 `_Singleton__instance` 语义 |

---

## 18. `utils/hz_sample.py` —— `HZSample`

| 方法 | 签名 | 说明 |
| :-- | :-- | :-- |
| `__init__(interval=1.0)` | — | 内部创建 `RecurrentThread` |
| `Start()` | — | 启动统计线程 |
| `Sample()` | — | 计数 +1；线程每秒打印 `HZ: <n/interval>` |

> 依赖 `utils.thread`，仅 Linux 可用。

---

## 19. `utils/joystick.py`

| 类/方法 | 签名 | 说明 |
| :-- | :-- | :-- |
| `Button.__call__(data)` | — | 更新 `pressed/on_pressed/on_released/click_count` |
| `Button.reset_click_count()` | — | 清零连击计数 |
| `Axis.__call__(data)` | — | 死区 `0.01`、平滑 `0.03`、阈值 `0.5` |
| `Joystick.extract(wireless_remote: list[int])` | — | 从 40 字节遥控数据解析按键/摇杆 |
| `Joystick.combine()` | `-> list[int]` | 打包为 40 字节 |
| `PyGameJoystick.__init__()` | — | 需要 `pygame` 与至少一个手柄；无手柄抛 `Exception("No joystick found!")` |
| `LogicJoystick.update()` | — | **R9：引用未定义的 `self.LS/self.RS`** |

> `pygame` 未在依赖中声明；`unitree_sdk2py/__init__.py` 不导入本模块，按需使用。

---

## 20. 平台相关模块（不可跨平台导入）

| 模块 | 约束 |
| :-- | :-- |
| `utils/timerfd.py` | 导入时 `CDLL(None)` 绑定 `timerfd_create/timerfd_settime`，仅 Linux |
| `utils/clib_lookup.py` | 同上，查找 libc 符号 |
| `utils/thread.py`、`utils/hz_sample.py` | 间接依赖 `timerfd`，仅 Linux |

---

## 21. 调用关系速查

```
用户脚本
  └─ ChannelFactoryInitialize(id, iface)
       └─ ChannelFactory.Init → Domain + DomainParticipant

*Client(ClientBase)
  ├─ ClientStub.Init
  │    ├─ CreateSendChannel("rt/api/<svc>/request", Request_)
  │    └─ CreateRecvChannel("rt/api/<svc>/response", Response_, handler, 10)
  └─ _Call → _CallBase → SendRequest → Future.GetResult

rpc.Server
  ├─ ServerStub.Init
  │    ├─ CreateSendChannel("rt/api/<svc>/response", Response_)
  │    └─ CreateRecvChannel("rt/api/<svc>/request", Request_, enqueue, 10)
  └─ handler(parameter) -> (code, data) → _SendResponse

LeaseClient / LeaseServer
  └─ 通道 "<svc>_lease"，apiId 101/102
```

> 详细的服务方法与 topic 表见 [robot-services.md](file:///e:/200_Coding/unitree_sdk2_python/contracts/robot-services.md)。

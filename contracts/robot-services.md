# contracts/robot-services.md —— 机器人服务与 DDS 契约

> 本文档冻结 `<robot>/<service>/` 下服务客户端的**对外方法、API ID、请求 JSON 键、返回形状**，
> 以及 DDS topic / 事件 / 定时任务契约。所有内容由当前代码只读反推，未修改任何业务代码。
> 全局规则（通道命名、RPC 错误码、IDL/CRC）见 [README.md](file:///e:/200_Coding/unitree_sdk2_python/contracts/README.md)，
> Python 层签名见 [python-api.md](file:///e:/200_Coding/unitree_sdk2_python/contracts/python-api.md)。

## 一、通用调用范式

```python
from unitree_sdk2py.core.channel import ChannelFactoryInitialize
from unitree_sdk2py.g1.loco.g1_loco_client import LocoClient

ChannelFactoryInitialize(0)      # id=0, 可选 networkInterface
client = LocoClient()            # 构造即确定 serviceName
client.Init()                    # 设置 apiVersion + 注册 API（缺此步则 3103）
client.SetTimeout(1.0)           # 可选，默认 1.0s
client.Damp()
```

固定顺序与语义：

| 步骤 | 行为 | 失败后果 |
| :-- | :-- | :-- |
| `ChannelFactoryInitialize(id, networkInterface=None)` | 初始化 DDS 域；失败抛 `Exception("channel factory init error.")` | 后续建通道失败 |
| `XxxClient(...)` | 仅保存 `serviceName`；`enableLease=True` 时构造内 `LeaseClient(service).Init()` 并启动租约线程 | — |
| `Init()` | `_SetApiVersion(version)` + 逐条 `_RegistApi(apiId, 0)` | 未注册的 `apiId > 100` 调用返回 `3103` |
| `WaitLeaseApplied()` | 仅在启用租约时需要；忙等 `sleep(0.1)` | 未持有租约时服务端返回 `3205` |
| `_Call(apiId, json)` | 同步等待响应，超时返回 `3104` | `data` 为空字符串 |
| `_CallNoReply(apiId, json)` | 只发不收；返回发送状态码 | 不产生 `3104` |

返回约定：

- 写类方法（`Damp`/`Move`/`SetXxx`）返回 `int` RPC 码，`0` 为成功。
- 读类方法返回 `(code, value)`；失败时 `value` 为 `None`。
- 特殊：`RobotStateClient.ServiceList()` 返回 `(code, List[ServiceState])`；
  `RobotStateClient.GetPkgVersion()` 返回 `(code, packageVersion, moduleVersionMap)`；
  `H2 LocoClient.GetAvailableFsmIds()` 返回 `(code, ids, names)`。

## 二、机型 → 客户端映射

| 机型 | 客户端 | service | 版本 | 说明 |
| :-- | :-- | :-- | :-- | :-- |
| go2 | `go2.sport.SportClient` | `sport` | `1.0.0.1` | 四足 |
| go2w | 复用 `go2.sport.SportClient` | `sport` | `1.0.0.1` | 无独立 Python 服务目录 |
| b2 | `b2.sport.SportClient` | `sport` | `1.0.0.1` | 四足 |
| b2w | 复用 `b2.sport.SportClient` | `sport` | `1.0.0.1` | 无独立 Python 服务目录 |
| a2 | `a2.sport.SportClient` | `sport` | `1.0.0.1` | 轮足 |
| as2 | `as2.sport.SportClient` | `sport` | `1.0.0.1` | 无 `__init__.py`（R14） |
| g1 | `g1.loco.LocoClient` | `sport` | `1.0.0.0` | 人形，API 7xxx |
| h1 | `h1.loco.LocoClient` | `loco` | `2.0.0.0` | 人形，API 8xxx |
| h2 | `h2.loco.LocoClient` | `sport` | `1.0.0.0` | 人形，API 7xxx |
| r1 | `r1.loco.LocoClient` | `sport` | `1.0.0.0` | 无 `__init__.py`（R14） |

> 注意：g1/h2/r1 的服务名都是 `sport` 但类名是 `LocoClient`；h1 的服务名是 `loco`。

## 三、go2 `SportClient`

`SportClient(enableLease: bool = False)`；常量 `SPORT_PATH_POINT_SIZE = 30`；
`PathPoint(timeFromStart, x, y, yaw, vx, vy, vyaw)`。

| 方法 | API ID | 请求 JSON | 返回 |
| :-- | :-- | :-- | :-- |
| `Damp()` | 1001 | `{}` | `int` |
| `BalanceStand()` | 1002 | `{}` | `int` |
| `StopMove()` | 1003 | `{}` | `int` |
| `StandUp()` | 1004 | `{}` | `int` |
| `StandDown()` | 1005 | `{}` | `int` |
| `RecoveryStand()` | 1006 | `{}` | `int` |
| `Euler(roll, pitch, yaw)` | 1007 | `{"x":roll,"y":pitch,"z":yaw}` | `int` |
| `Move(vx, vy, vyaw)` | 1008 | `{"x":vx,"y":vy,"z":vyaw}` | `int`（**NoReply**） |
| `Sit()` | 1009 | `{}` | `int` |
| `RiseSit()` | 1010 | `{}` | `int` |
| `SpeedLevel(level)` | 1015 | `{"data":level}` | `int` |
| `Hello()` | 1016 | `{}` | `int` |
| `Stretch()` | 1017 | `{}` | `int` |
| `TrajectoryFollow(path)` | 1018 | `[{"t_from_start","x","y","yaw","vx","vy","vyaw"}, ...]` | `int`（**NoReply**）；长度≠30 返回 `4101` |
| `Content()` | 1020 | `{}` | `int` |
| `Dance1()` | 1022 | `{}` | `int` |
| `Dance2()` | 1023 | `{}` | `int` |
| `SwitchJoystick(on)` | 1027 | `{"data":on}` | `int` |
| `Pose(flag)` | 1028 | `{"data":flag}` | `int` |
| `Scrape()` | 1029 | `{}` | `int` |
| `FrontFlip()` | 1030 | `{}` | `int` |
| `FrontJump()` | 1031 | `{}` | `int` |
| `FrontPounce()` | 1032 | `{}` | `int` |
| `Heart()` | 1036 | `{}` | `int` |
| `StaticWalk()` | 1061 | `{}` | `int` |
| `TrotRun()` | 1062 | `{}` | `int` |
| `EconomicGait()` | 1063 | `{}` | `int` |
| `LeftFlip()` | 2041 | `{}` | `int` |
| `BackFlip()` | 2043 | `{}` | `int` |
| `HandStand(flag)` | 2044 | `{"data":flag}` | `int` |
| `FreeWalk()` | 2045 | `{}` | `int` |
| `FreeBound(flag)` | 2046 | `{"data":flag}` | `int` |
| `FreeJump(flag)` | 2047 | `{"data":flag}` | `int` |
| `FreeAvoid(flag)` | 2048 | `{"data":flag}` | `int` |
| `ClassicWalk(flag)` | 2049 | `{"data":flag}` | `int` |
| `WalkUpright(flag)` | 2050 | `{"data":flag}` | `int` |
| `CrossStep(flag)` | 2051 | `{"data":flag}` | `int` |
| `AutoRecoverySet(enabled)` | 2054 | `{"data":enabled}` | `int` |
| `AutoRecoveryGet()` | 2055 | `{}` | `(int, data)` |
| `SwitchAvoidMode()` | 2058 | `{}` | `int` |

## 四、b2 `SportClient`

`SportClient(enableLease: bool = False)`；`SPORT_PATH_POINT_SIZE = 30`；`PathPoint` 同 go2。

| 方法 | API ID | 请求 JSON | 返回 |
| :-- | :-- | :-- | :-- |
| `Damp()` | 1001 | `{}` | `int` |
| `BalanceStand()` | 1002 | `{}` | `int` |
| `StopMove()` | 1003 | `{}` | `int` |
| `StandUp()` | 1004 | `{}` | `int` |
| `StandDown()` | 1005 | `{}` | `int` |
| `RecoveryStand()` | 1006 | `{}` | `int` |
| `Move(vx, vy, vyaw)` | 1008 | `{"x":vx,"y":vy,"z":vyaw}` | `int`（**NoReply**） |
| `SwitchGait(t)` | 1011 | `{"data":t}` | `int` |
| `BodyHeight(height)` | 1013 | `{"data":height}` | `int` |
| `SpeedLevel(level)` | 1015 | `{"data":level}` | `int` |
| `TrajectoryFollow(path)` | 1018 | 同 go2 | `int`（**NoReply**）；长度≠30 返回 `4101` |
| `ContinuousGait(flag)` | 1019 | `{"data":flag}` | `int` |
| `MoveToPos(x, y, yaw)` | 1036 | `{"x":x,"y":y,"yaw":yaw}` | `int` |
| `SwitchMoveMode(flag)` | 1038 | `{"data":flag}` | `int` |
| `HandStand(flag)` | 1039 | `{"data":flag}` | `int` |
| `AutoRecoverySet(flag)` | 1040 | `{"data":flag}` | `int` |
| `FreeWalk()` | 1045 | `{"data":true}` | `int` |
| `ClassicWalk(flag)` | 1049 | `{"data":flag}` | `int` |
| `FastWalk(flag)` | 1050 | `{"data":flag}` | `int` |
| `FreeEuler(flag)` | 1051 | `{"data":flag}` | `int` |
| `VisionWalk(flag)` | 1101 | `{"data":flag}` | `int` |

## 五、a2 / as2 `SportClient`

两者方法集基本一致；`as2` 额外注册并暴露 `SwitchJoystick`。
**与 go2/b2 的关键差异**：`Move` 使用 `_Call`（等待响应），不是 `_CallNoReply`。

| 方法 | API ID | 请求 JSON | 返回 |
| :-- | :-- | :-- | :-- |
| `Damp()` / `BalanceStand()` / `StopMove()` / `StandUp()` / `StandDown()` / `RecoveryStand()` | 1001–1006 | `{}` | `int` |
| `Euler(roll, pitch, yaw)` | 1007 | `{"x":roll,"y":pitch,"z":yaw}` | `int` |
| `Move(vx, vy, vyaw)` | 1008 | `{"x":vx,"y":vy,"z":vyaw}` | `int`（**有响应**） |
| `BodyPosition(x, y, z, yaw)` | 1009 | `{"x","y","z","yaw"}` | `int` |
| `SwitchGait(gait_type)` | 1011 | `{"data":gait_type}` | `int` |
| `BodyHeight(height)` | 1013 | `{"data":height}` | `int` |
| `SpeedLevel(level)` | 1015 | `{"data":level}` | `int` |
| `LeftSideGait(enter)` | 1016 | `{"data":enter}` | `int` |
| `RightSideGait(enter)` | 1017 | `{"data":enter}` | `int` |
| `HandStand(enter)` | 1018 | `{"data":enter}` | `int` |
| `BipedStand(enter)` | 1019 | `{"data":enter}` | `int` |
| `FrontFlip()` | 1020 | `{}` | `int` |
| `BackFlip()` | 1021 | `{}` | `int` |
| `GetState(state_map)` | 1034 | `{}` | `int`；成功时把响应 JSON 就地更新进 `state_map` |
| `SetAutoRecovery(switch_on)` | 1040 | `{"data":switch_on}` | `int` |
| `SwitchJoystick(switch_on)`（仅 as2） | 1041 | `{"data":switch_on}` | `int` |

## 六、g1 `LocoClient`

`LocoClient()`；`InternalFsmMode`：`LAST=0`、`PASSIVE=1`、`WALKRUN=2`。

| 方法 | API ID | 请求 JSON | 返回 |
| :-- | :-- | :-- | :-- |
| `GetFsmId()` | 7001 | `{}` | `(int, data)` |
| `SetFsmId(fsm_id)` | 7101 | `{"data":fsm_id}` | `int` |
| `SetBalanceMode(balance_mode)` | 7102 | `{"data":balance_mode}` | `int` |
| `SetStandHeight(stand_height)` | 7104 | `{"data":stand_height}` | `int` |
| `SetVelocity(vx, vy, omega, duration=1.0)` | 7105 | `{"velocity":[vx,vy,omega],"duration":duration}` | `int` |
| `SetTaskId(task_id)` | 7106 | `{"data":task_id}` | `int` |
| `SetSpeedMode(speed_mode)` | 7107 | `{"data":speed_mode}` | `int` |
| `SwitchToUserCtrl()` | 7110 | `{"data":false}` | `int` |
| `SwitchToInternalCtrl(mode)` | 7111 | `{"data":0/1/2}` | `int`；非法 `mode` 抛 `ValueError` |

便捷方法（均为 `SetFsmId` / `SetStandHeight` / `SetVelocity` / `SetTaskId` 的封装）：

| 方法 | 实际请求 | 说明 |
| :-- | :-- | :-- |
| `Damp()` | FSM `1` | — |
| `Start()` | FSM `500` | — |
| `ZeroTorque()` | FSM `0` | — |
| `Sit()` | FSM `3` | — |
| `Lie2StandUp()` | FSM `702` | — |
| `Squat2StandUp()` | FSM `706` | 与 `StandUp2Squat()` 同值 |
| `StandUp2Squat()` | FSM `706` | 与 `Squat2StandUp()` 同值 |
| `StopMove()` | `SetVelocity(0,0,0)` | — |
| `HighStand()` | `SetStandHeight(0xFFFFFFFF)` | 由固件解释为“最高” |
| `LowStand()` | `SetStandHeight(0)` | — |
| `Move(vx, vy, vyaw, continous_move=False)` | `duration = 864000.0` 或 `1` | — |
| `BalanceStand(balance_mode)` | `SetBalanceMode(balance_mode)` | — |
| `WaveHand(turn_flag=False)` | `SetTaskId(1/0)` | — |
| `ShakeHand(stage=-1)` | `SetTaskId(2/3)` | `stage=-1` 时在 2/3 间切换 |

> **C7**：`Init()` 注册了 7002–7006（FSM Mode / Balance Mode / Swing Height / Stand Height / Phase）
> 与 7103（Swing Height），但未提供对应公开方法。属“已注册未暴露”，不影响既有调用方。

## 七、h1 `LocoClient`

service `loco`，版本 `2.0.0.0`。

| 方法 | API ID | 请求 JSON | 返回 |
| :-- | :-- | :-- | :-- |
| `SetFsmId(fsm_id)` | 8101 | `{"data":fsm_id}` | `int` |
| `SetStandHeight(stand_height)` | 8104 | `{"data":stand_height}` | `int` |
| `SetVelocity(vx, vy, omega, duration=1.0)` | 8105 | `{"velocity":[vx,vy,omega],"duration":duration}` | `int` |
| `Damp()` | 8101 | FSM `1` | `int` |
| `Start()` | 8101 | FSM `204` | `int` |
| `StandUp()` | 8101 | FSM `2` | `int` |
| `ZeroTorque()` | 8101 | FSM `0` | `int` |
| `StopMove()` | 8105 | `[0,0,0]` | `int` |
| `HighStand()` / `LowStand()` | 8104 | `0xFFFFFFFF` / `0` | `int` |
| `Move(vx, vy, vyaw, continous_move=False)` | 8105 | `duration` 864000 / 1 | `int` |

> **C4**：注册了 8001–8006、8102、8103，但未暴露任何 GET 方法与 `SetBalanceMode`/`SetSwingHeight`。

## 八、h2 `LocoClient`

service `sport`，版本 `1.0.0.0`；业务错误码 `7301`–`7303`。

| 方法 | API ID | 请求 JSON | 返回 |
| :-- | :-- | :-- | :-- |
| `GetFsmId()` / `GetFsmMode()` / `GetBalanceMode()` / `GetSwingHeight()` / `GetStandHeight()` / `GetPhase()` / `GetArmSdkStatus()` | 7001–7007 | `{}` | `(int, data)` |
| `GetAvailableFsmIds()` | 7008 | `{}` | `(int, ids, names)` |
| `SetFsmId(fsm_id)` | 7101 | `{"data":fsm_id}` | `int` |
| `SetBalanceMode(mode)` | 7102 | `{"data":mode}` | `int` |
| `SetSwingHeight(h)` | 7103 | `{"data":h}` | `int` |
| `SetStandHeight(h)` | 7104 | `{"data":h}` | `int` |
| `SetVelocity(vx, vy, omega, duration=1.0)` | 7105 | `{"velocity":[...],"duration":...}` | `int` |
| `SetTaskId(task_id)` | 7106 | `{"data":task_id}` | `int` |
| `SetSpeedMode(mode)` | 7107 | `{"data":mode}` | `int` |
| `SetPunchApi(punch_api)` | 7108 | `{"data":punch_api}` | `int` |
| `SetArmSdkStatus(status)` | 7109 | `{"data":status}` | `int` |
| `Damp()` | 7101 | FSM `1` | `int` |
| `Start()` | 7101 | FSM `601` | `int` |
| `Squat()` | 7101 | FSM `2` | `int` |
| `Sit()` | 7101 | FSM `3` | `int` |
| `StandUp()` | 7101 | FSM `4` | `int` |
| `ZeroTorque()` | 7101 | FSM `0` | `int` |
| `HighStand()` / `LowStand()` | 7104 | `0xFFFFFFFF` / `0` | `int` |
| `Move(vx, vy, vyaw, continous_move=None)` | 7105 | 未传时沿用 `self.continous_move_` | `int` |
| `BalanceStand()` / `ContinuousGait(flag)` | 7102 | mode `0` / `1` 或 `0` | `int` |
| `SwitchMoveMode(flag)` | — | **不发起 RPC**，只改本地 `continous_move_` | `0` |
| `WaveHand(turn_flag=False)` | 7106 | task `1/0` | `int` |
| `ShakeHand(stage=-1)` | 7106 | task `2/3` | `int` |
| `EnableArmSDK()` / `DisableArmSDK()` | 7109 | `{"data":true}` / `{"data":false}` | `int` |

## 九、r1 `LocoClient`

service `sport`，版本 `1.0.0.0`。

| 方法 | API ID | 请求 JSON | 返回 |
| :-- | :-- | :-- | :-- |
| `SetFsmId(fsm_id)` | 7101 | `{"data":fsm_id}` | `int` |
| `SetVelocity(vx, vy, omega, duration=1.0)` | 7105 | `{"velocity":[...],"duration":...}` | `int` |
| `SetTaskId(task_id)` | 7106 | `{"data":task_id}` | `int` |
| `Damp()` | 7101 | FSM `1` | `int` |
| `Stance()` | 7101 | FSM `4` | `int` |
| `Start()` | 7101 | FSM `811` | `int` |
| `Lie2StandUp()` | 7101 | FSM `701` | `int` |
| `StandUp2Lie()` | 7101 | FSM `702` | `int` |
| `ZeroTorque()` | 7101 | FSM `0` | `int` |
| `StopMove()` | 7105 | `[0,0,0]` | `int` |
| `Move(vx, vy, vyaw, continous_move=False)` | 7105 | `duration` 864000 / 1 | `int` |
| `WaveHand(turn_flag=False)` | 7106 | task `1/0` | `int` |
| `ShakeHand(stage=-1)` | 7106 | task `2/3` | `int` |

> `r1.loco` 注册了 7001（GET FSM ID）但未暴露 getter。

## 十、`motion_switcher`

`MotionSwitcherClient()`；service `motion_switcher`，版本 `1.0.0.1`。

| 方法 | API ID | 请求 JSON | 返回 |
| :-- | :-- | :-- | :-- |
| `CheckMode()` | 1001 | `{}` | `(int, dict)` |
| `SelectMode(nameOrAlias)` | 1002 | `{"name":nameOrAlias}` | `(int, None)` |
| `ReleaseMode()` | 1003 | `{}` | `(int, None)` |

> **C8**：`Init()` 注册了 1004 `SET_SILENT`、1005 `GET_SILENT`，但无对应公开方法。

## 十一、`robot_state`

### 11.1 go2（版本 `1.0.0.1`）

`RobotStateClient()`；`ServiceState(name, status, protect)`。

| 方法 | API ID | 请求 JSON | 返回 |
| :-- | :-- | :-- | :-- |
| `ServiceList()` | 1003 | `{}` | `(int, List[ServiceState])` |
| `ServiceSwitch(name, switch)` | 1001 | `{"name":name,"switch":int(switch)}` | `int`；`status==5` → `5202`；`status∉{0,1}` → `5201` |
| `SetReportFreq(interval, duration)` | 1002 | `{"interval":interval,"duration":duration}` | `int` |

### 11.2 b2（版本 `1.0.0.2`）

额外两个方法与六个 API 注册：

| 方法 | API ID | 请求 JSON | 返回 |
| :-- | :-- | :-- | :-- |
| `LowPowerSwitch(swit)` | 1004 | `{"switch":swit}` | `int` |
| `LowPowerStatus()` | 1005 | `{}` | `(int, status)` |
| `GetPkgVersion()` | 1006 | `{}` | `(int, packageVersion, moduleVersionMap)` |

> `ServiceList` / `ServiceSwitch` / `SetReportFreq` 与 go2 完全一致（1003/1001/1002）。

## 十二、`obstacles_avoid`

`ObstaclesAvoidClient()`；service `obstacles_avoid`，版本 `1.0.0.2`。

| 方法 | API ID | 请求 JSON | 返回 |
| :-- | :-- | :-- | :-- |
| `SwitchSet(on)` | 1001 | `{"enable":on}` | `int` |
| `SwitchGet()` | 1002 | `{}` | `(int, enable)` |
| `Move(vx, vy, vyaw)` | 1003 | `{"x":vx,"y":vy,"yaw":vyaw,"mode":0}` | `int`（**NoReply**） |
| `MoveToIncrementPosition(vx, vy, vyaw)` | 1003 | 同上，`mode=1` | `int`（**NoReply**） |
| `MoveToAbsolutePosition(vx, vy, vyaw)` | 1003 | 同上，`mode=2` | `int`（**NoReply**） |
| `UseRemoteCommandFromApi(flag)` | 1004 | `{"is_remote_commands_from_api":flag}` | `int` |

> 与 `sport.Move` 的键不同：这里是 `x/y/yaw`，sport 是 `x/y/z`。

## 十三、视频服务

| 客户端 | service | 版本 | 方法 | API ID | 返回 |
| :-- | :-- | :-- | :-- | :-- | :-- |
| `go2.video.VideoClient` | `videohub` | `1.0.0.1` | `GetImageSample()` | 1001 | `_CallBinary` 原始二进制 |
| `b2.front_video.FrontVideoClient` | `front_videohub` | `1.0.0.0` | `GetImageSample()` | 1001 | 同上 |
| `b2.back_video.BackVideoClient` | `back_videohub` | `1.0.0.0` | `GetImageSample()` | 1001 | 同上 |

## 十四、`vui`（go2 / b2）

`VuiClient()`；service `vui`，版本 `1.0.0.1`。

| 方法 | API ID | 请求 JSON | 返回 |
| :-- | :-- | :-- | :-- |
| `SetSwitch(enable)` | 1001 | `{"enable":enable}` | `int` |
| `GetSwitch()` | 1002 | `{}` | `(int, enable)` |
| `SetVolume(level)` | 1003 | `{"volume":level}` | `int` |
| `GetVolume()` | 1004 | `{}` | `(int, volume)` |
| `SetBrightness(level)` | 1005 | `{"brightness":level}` | `int` |
| `GetBrightness()` | 1006 | `{}` | `(int, brightness)` |

## 十五、音频服务（a2 / g1）

`AudioClient()`；service `voice`，版本 `1.0.0.0`。

| 方法 | API ID | 请求 | 返回 |
| :-- | :-- | :-- | :-- |
| `TtsMaker(text, speaker_id)` | 1001 | `{"index","text","speaker_id"}` | `int` |
| `GetVolume()` | 1005 | `{}` | `(int, dict)` |
| `SetVolume(volume)` | 1006 | `{"volume":volume}` | `int` |
| `LedControl(R, G, B)` | 1010 | `{"R","G","B"}` | `int` |
| `PlayStream(app_name, stream_id, pcm_data)` | 1003 | JSON `{"app_name","stream_id"}` + binary `pcm_list` | `_CallRequestWithParamAndBin` 结果 |
| `PlayStop(app_name)` | 1004 | `{"app_name":app_name}` | 恒为 `0`（**C2**） |

> `TtsMaker` 的 `index`：a2 自增 `+1`；g1 为自乘 `+= self.tts_index`（**C3**）。
> 业务错误码 `AUDIO_ERR_COMM = 100` 仅定义在 a2。

## 十六、g1 手臂动作

`G1ArmActionClient()`；service `arm`，版本 `1.0.0.14`。

| 方法 | API ID | 请求 JSON | 返回 |
| :-- | :-- | :-- | :-- |
| `ExecuteAction(action_id)` | 7106 | `{"data":action_id}` | `int` |
| `GetActionList()` | 7107 | `{}` | `(int, list)` |

模块级 `action_map`（名称 → id，共 16 项）：
`release arm=99`、`two-hand kiss=11`、`left kiss=12`、`right kiss=13`、`hands up=15`、
`clap=17`、`high five=18`、`hug=19`、`heart=20`、`right heart=21`、`reject=22`、
`right hand up=23`、`x-ray=24`、`face wave=25`、`high wave=26`、`shake hand=27`。

## 十七、业务错误码速查

| 模块 | 数值 | 常量 | 含义 |
| :-- | :-- | :-- | :-- |
| go2/b2 `sport` | 4101 | `SPORT_ERR_CLIENT_POINT_PATH` | 轨迹点数量≠30（客户端本地） |
| go2/b2 `sport` | 4201 | `SPORT_ERR_SERVER_OVERTIME` | 服务端超时 |
| go2/b2 `sport` | 4202 | `SPORT_ERR_SERVER_NOT_INIT` | 服务端未初始化 |
| a2/as2 `sport` | 4201 | `SPORT_ERR_SERVER_OVERTIME` | 服务端超时 |
| a2/as2 `sport` | 4205 | `SPORT_ERR_SERVER_NOT_INIT` | 服务端未初始化（**与四足 4202 不同**） |
| go2/b2 `robot_state` | 5201 | `ROBOT_STATE_ERR_SERVICE_SWITCH` | 服务切换失败 |
| go2/b2 `robot_state` | 5202 | `ROBOT_STATE_ERR_SERVICE_PROTECTED` | 服务受保护 |
| h2 `loco` | 7301 | `LOCO_ERR_LOCOSTATE_NOT_AVAILABLE` / `LOCO_ERR_SCHEDULER_STATE_NOT_AVAILABLE` | 状态不可用（两个常量同值） |
| h2 `loco` | 7302 | `LOCO_ERR_INVALID_FSM_ID` | FSM ID 非法 |
| h2 `loco` | 7303 | `LOCO_ERR_INVALID_TASK_ID` | Task ID 非法 |
| a2 `audio` | 100 | `AUDIO_ERR_COMM` | 音频通信错误 |

## 十八、DDS topic 契约

| topic | 方向（SDK 视角） | IDL 类型 | 使用方 / 示例 |
| :-- | :-- | :-- | :-- |
| `rt/lowcmd` | 发布 | `unitree_go.msg.dds_.LowCmd_`（go2/go2w/b2/b2w/a2/as2/r1/h1）或 `unitree_hg.msg.dds_.LowCmd_`（g1/h1_2/h2） | `example/*/low_level/*_stand_example.py` 等 |
| `rt/lowstate` | 订阅 | 与 `rt/lowcmd` 同族（go 20 电机 / hg 35 电机） | 所有 low_level 示例 |
| `rt/lf/lowstate` | 订阅 | `unitree_go.msg.dds_.LowState_` | `example/wireless_controller/wireless_controller.py` |
| `rt/arm_sdk` | 发布 | `unitree_hg.msg.dds_.LowCmd_` | `example/g1/high_level/g1_arm{5,7}_sdk_dds_example.py`、`example/h2/high_level/h2_arm_sdk_dds_example.py` |
| `rt/secondary_imu` | 订阅 | `unitree_hg.msg.dds_.IMUState_` | `example/h2/low_level/h2_ankle_swing_example.py` |
| `rt/utlidar/switch` | 发布 | `std_msgs.msg.dds_.String_` | `example/go2/high_level/go2_utlidar_switch.py` |
| `rt/lf/sportmodestate` | 订阅 | `unitree_go.msg.dds_.SportModeState_` | `example/a2/sport/a2_sport_state.py`、`example/as2/sport/as2_sport_state.py` |
| `topic` | 双向 | 用户自定义 IDL（示例为 `UserData`） | `example/helloworld/{publisher,subscriber}.py` |
| `rt/api/<service>/request` | 客户端发 / 服务端收 | `unitree_api.msg.dds_.Request_` | `rpc/client_stub.py`、`rpc/server_stub.py` |
| `rt/api/<service>/response` | 服务端发 / 客户端收 | `unitree_api.msg.dds_.Response_` | 同上 |
| `<service>_lease` | 双向 | `unitree_api.msg.dds_.Request_` / `Response_` | `rpc/lease_client.py`、`rpc/lease_server.py` |

> topic 名称与 IDL 类型均视为冻结项；CRC 只支持 `rt/lowcmd`/`rt/lowstate` 的 4 种消息，
> 字节数见 [README.md](file:///e:/200_Coding/unitree_sdk2_python/contracts/README.md#L139-L152)。

## 十九、事件与定时任务契约

| 事件 / 定时任务 | 来源 | 触发与周期 | 可停止性 |
| :-- | :-- | :-- | :-- |
| RPC 响应回调 | `rpc/client_stub.py` | 收到 `rt/api/<service>/response` 即 `RequestFuture.Set(requestId, ...)` | 随 `Close()` 结束 |
| RPC 请求处理线程 | `rpc/server_base.py` | `Start()` 后常驻，从 `BQueue` 取请求 | 无公开停止接口 |
| 租约申请/续约 | `rpc/lease_client.py` | 守护线程，申请成功后续约周期 `term * 0.3`；`term` 服务端为 `int(term*1e6)` 微秒 | **不可停止**（R10） |
| DDS 订阅回调 | `core/channel.py` `__Reader.__OnDataAvailable` | 每收到一条样本调用一次 handler | `ChannelSubscriber.Close()` |
| `RecurrentThread` | `utils/thread.py` | 周期 `interval` 秒，基于 Linux `timerfd` | `Wait(timeout)` 置 quit；**Windows 不可用** |
| `HZSample` | `utils/hz_sample.py` | 内部 `RecurrentThread(interval=1.0)` 采样频率统计 | 跟随 `RecurrentThread` |

---

## 二十、基线

- 代码版本：`unitree_sdk2py` 1.0.1
- 冻结日期：2026-10-22
- 本次操作：**仅新增文档，未修改任何业务代码**

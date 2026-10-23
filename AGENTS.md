# AGENTS.md —— 遗留系统改造

> 若项目根目录存在 `init.md`，说明尚未完成改造准备：请先按 `init.md` 的引导完成
> 四步准备，再开始小步改造。准备完成后自动删除 `init.md`。

## 一、本项目采用的开发理念

改老系统与写新项目相反——先"认知与保护"，再"小步改造"，理念组合如下：

| 理念 | 在本项目解决什么 | 落地形态 |
| :-- | :-- | :-- |
| **反向文档生成** | 从现有代码反推认知，摸清家底 | README.md + ARCHITECTURE.md |
| **CDD** | 冻结对外接口契约，防止改造破坏调用方 | `contracts/` 接口清单 |
| **Harness（基础档）** | 用红线和禁令约束 AI 改造行为 | 本文件「二、现状约束」 |
| **TDD 补测** | 改前先补测试安全网 | 核心路径单元测试 |
| **SDD 增量** | 每步改造先出规格，小步可回滚 | 每步 Spec |

**适配说明**：本场景最忌"大拆大改、一把梭"。红线（不升级框架/不改公共接口）
是硬约束，不可裁剪；其余按本次改造范围取舍。

## 二、现状约束（标准必备内容，长期生效）

> 本节已按 `init.md` 第 3 步补全；数据来源：`pyproject.toml`、`contracts/`、`ARCHITECTURE.md`。

### 2.1 技术栈与版本（禁止升级）

| 项 | 值 |
| :-- | :-- |
| 语言 | Python >= 3.8（`requires-python`）；开发环境 3.10（`.python-version`） |
| 通信中间件 | `cyclonedds == 0.10.2`（版本锁定） |
| 数据模型 | `unitree_go`（20 电机）、`unitree_hg`（35 电机）、`unitree_api`（RPC 报文） |
| 运行依赖 | `numpy`、`opencv-python`；手柄示例另需 `pygame`（未写入依赖声明） |
| 打包 | setuptools + wheel，`pyproject.toml`，版本 `1.0.1`，BSD-3-Clause |
| 平台约束 | CRC 加速 `.so` 与 `timerfd` 周期线程仅 Linux；Windows 无 `RecurrentThread` |
| 测试设施 | 无 pytest 配置、无 CI（R16）；`unitree_sdk2py/test/` 为手工脚本 |

### 2.2 禁止事项

- **不许升级框架/运行时**：不改 `cyclonedds` 版本、不改 `requires-python`、不引入新通信栈。
- **不许改公共接口**：不改 `contracts/` 冻结的方法签名、返回元组形状、服务名、API 版本、API ID、请求 JSON 键名。
- **不许改 IDL 与 CRC**：不改 `idl/` 字段顺序/类型/长度，不改 `utils/crc.py` 的 4 种 pack 格式与字节数。
- **不许改 DDS 契约**：不改 topic 名称、IDL 类型与收发方向。
- **不许重构无关代码**：不"顺手"格式化、不批量重命名、不删除未使用方法（C4/C7/C8 只登记不处理）。
- **不许大改**：单步改动不超过 **3** 个文件。

### 2.3 构建与测试命令

| 用途 | 命令 |
| :-- | :-- |
| 本机运行环境 | `.venv\Scripts\python.exe`（Python 3.10.21，`cyclonedds` 已装，`import unitree_sdk2py` 通过） |
| 安装（开发） | `pip install -e .` |
| 安装（uv） | `uv sync` |
| 构建 | `python -m build` |
| 导入自检 | `python -c "import unitree_sdk2py; print(unitree_sdk2py.__file__)"` |
| 现有脚本自检 | `python unitree_sdk2py/test/crc/test_crc.py` |
| 单元测试 | `.venv\Scripts\python.exe -m unittest discover -s unitree_sdk2py/test/unit -t unitree_sdk2py/test/unit -v` |

> `pip install -e .` 报 `Could not locate cyclonedds` 时，先编译 CycloneDDS 并设置 `CYCLONEDDS_HOME`。

### 2.4 改造红线

- [x] 禁止升级框架/运行时版本
- [x] 禁止修改公共接口签名（`contracts/` 中冻结项）
- [x] 禁止一次性重写超过 **3** 个文件
- [x] 禁止未经 Spec 与确认的改动；每步改动必须可独立回滚
- [x] 禁止在 DDS 回调线程内做阻塞长任务

## 三、小步改造规则（长期生效）

每次改动遵循：先出该步 Spec（保持对外接口不变）→ 我确认 → 实现 → 运行全部测试 →
通过则汇报，失败按 Ralph Loop 自修（上限 5 次）。每步改动保持可独立回滚。

不做任何未出 Spec、未经我确认的改动；不因"顺手"重构冻结接口或红线之外的代码。
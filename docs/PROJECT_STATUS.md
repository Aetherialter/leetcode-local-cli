# 项目状态

当前源码已准备版本 `v0.12.0`，主题是编辑器配置、节点本地调用与边界加固（等待维护者明确授权后打标签并触发发布；此前 GitHub Releases 与 PyPI 最新公开版本仍为 `v0.11.0`）。实际发布记录见 [GitHub Releases](https://github.com/Aetherialter/leetcode-local-cli/releases) 和 [PyPI](https://pypi.org/project/leetcode-local-cli/)。

## 当前能力

- 配置单个默认工作区并安全维护 `solution.py`，用户配置（v2）可跨工作区保留个人编辑器设置（`lc config editor`）。
- 通过日常 Chrome、日常 Edge 或手动 Cookie 登录 LeetCode 中文站。
- 查询题目、生成 Python3 模板、本地调用（含 `ListNode` / `TreeNode` 节点数组自动转换与可定位错误行号/可选调用栈）、环境诊断和远程提交。
- `cli.py → commands/ → use_cases/` 与 `models / storage / integrations / execution` 已形成职责分层，依赖方向由 AST 测试约束。
- 提交使用结构化结果和单调时钟总预算；超时或轮询失败保留 submission ID。
- 可用 `lc check <Submission ID>` 单次重新查询已有提交，不会重复发送代码。

## v0.12.0 变化

- 新增 `lc config editor`：支持 Zed、VS Code 和可执行文件路径/参数数组。用户配置不再强制含默认工作区，编辑器设置可在初始化前保存，之后 `init` 保留设置。
- `solve --editor` 临时覆盖用户设置，`--no-open` 优先；未配置只保存并提示，不再使用可能执行 `.py` 的系统文件关联。显式编辑器失败仍为保存成功加警告。
- `test` 支持通过 `ListNode` / `TreeNode` 可空或字符串注解进行节点数组转换，兼容 `null` / `None`，输出节点和原地修改参数可读。模板辅助定义位于提交区域外。
- 节点支持限定为整数值、无环单链表和普通二叉树；拒绝环、共享节点身份、嵌套集合及超限输入输出，不扩展到复杂节点或设计题协议。
- 本地异常增加用户代码行号；`test --verbose` 提供不采集局部变量的调用栈，JSON Lines 增加对应结构化字段。
- wheel/sdist 隔离 smoke test 新增编辑器设置跨初始化保留、节点模板资源和树数组调用验证。
- 用户配置独立写为 v2，marker 保持 v1、Session 不变；已有 v1 用户配置只读可用，显式设置/清除编辑器或初始化时才升级，防止旧版误用修复流程丢失新版字段。
- 编辑器参数补齐 TOML 控制字符转义，用户配置在原子替换前验证 UTF-8、TOML 与结构；序列化或替换失败保留原件。
- 普通与延迟注解一致拒绝包含引号的嵌套节点类型，`Literal` 取值与 `Annotated` 元数据不误判为类型引用；worker 超时后的重启加载错误保留行号与可选调用栈，后续输入仍可恢复。
- 发布工作流的三平台前置任务补齐 wheel/sdist 完整隔离安装验收，覆盖配置、初始化及节点调用；发布任务仍复验它自身构建的产物。
- 正确性加固：
  - `solution.py` 提交解析改用 `tokenize` 词法扫描识别提交区域外头部 `# @lc` 元数据与独立提交标记，跟踪 f-string 嵌套深度并拒绝未闭合 f-string/字符串，忽略字符串字面量（含 f-string 内部注释）与行内注释，拒绝缺失、重复或逆序标记，且保留未闭合括号等既有语法检查策略与原文件不覆盖原则。
  - GraphQL 请求区分 HTTP 200 与非空 `errors`（结构化映射为 `ClientErrorKind.GRAPHQL_ERROR`），不输出原始服务端错误信息；题目详情校验必需题目标识字段，缺少 Python3 模板时允许 `lc get` 查看但阻止 `lc solve` 写入 `solution.py`。
  - DevTools 登录单次浏览器尝试共用 180 秒单调时钟 `deadline`（覆盖连接、等待、重试与轮询），打开浏览器授权页后按当前单调时钟重算剩余预算以防超时后继续等待，保留 Chrome → Edge → 手动回退的逐浏览器独立预算，并明确 `close_timeout` 与在线账号校验（10 秒超时）不在轮询硬上限内。
  - `lc solve` 对生效的非法 `--editor` CLI 传参返回用法错误退出码 2，`--no-open` 仍优先跳过该校验；损坏的本地用户配置编辑器设置仍返回运行错误退出码 1，保存成功但编辑器启动失败仍警告并退出 0。
  - 修复 Linux/macOS 纳秒级 `monotonic()` 导致的既有 `test_cli.py` 授权端点测试浮点严格相等失败，完成 `v0.12.0` 版本与发布说明整理（见 [v0.12.0 Release Notes](release-notes/v0.12.0.md)）。
  - 针对真实环境验收反馈的发布前收敛修复：
    - `lc check` 对 `PENDING` / `STARTED` 不再断言“提交仍在判题中”，而是明确提示“暂未取得可确认的判题结果。提交可能仍在处理，或对当前账号不可见，请确认提交 ID 和账号”；不凭缺失 `status_msg` 推断提交不存在，继续保留 Submission ID、退出码 1 和单次查询行为，`lc submit` 提交后自动轮询仍继续等待直至判题完成或超时。
    - 区分明确认证失效（HTTP `401` 及 GraphQL `extensions.code == "UNAUTHENTICATED"` -> `ClientErrorKind.UNAUTHORIZED`，提示重新执行 `lc login`）与权限拒绝（HTTP `403` 及 GraphQL `extensions.code` 为 `FORBIDDEN` / `PERMISSION_DENIED` -> `ClientErrorKind.FORBIDDEN`，提示检查当前账号权限或登录状态且不承诺重登录必定解决），不解析自然语言错误文本，不输出原始服务端响应；`submit` 初始 POST 仍不自动重试，轮询对 `401`/`403` 也不重试；`lc doctor` 同步区分连通性通过与 `401`/`403` 失败提示。
    - 修正 [README](../README.md)、[产品边界](PRODUCT_BOUNDARIES.md) 与 [安全边界](SECURITY_REVIEW.md) 中关于 Session 与题目命令的说明：题目命令（`show`/`get`/`solve`）仅校验本地 `session.json` 格式而不预先在线验签；远端登录态与 Cookie 实际对应账号由 `status`/`profile`/`doctor` 确认（注意区分浏览器账号、`session.json` 保存用户名与 Cookie 实际对应的远端账号）。
    - `lc login` 手动 Cookie 回退在 `sys.stdin` 非交互式终端下立即提示并以退出码 1 快速失败，不通过 `getpass` 阻塞控制台也不从管道读取明文 Cookie；交互输入触发 `EOFError` 亦干净退出 1，失败不覆盖已有 `session.json`。

用户命令和限制见 [README](../README.md)，模块结构见 [ARCHITECTURE](ARCHITECTURE.md)。

## v0.11.0 变化

- 浏览器自动登录会先显示 Chrome/Edge 的 Remote debugging 设置地址，并明确要求勾选 **Allow remote debugging for this browser instance**；自动打开页面未显示或授权端点不可用时，也会提示用户手动打开对应地址。
- README 已记录 Chrome 的 `chrome://inspect/#remote-debugging` 和 Edge 的 `edge://inspect/#remote-debugging` 首次授权步骤。
- Session 已从工作区迁移到平台用户状态目录；账号、题目查询、提交结果查询和默认诊断不再依赖工作区初始化。
- 工作区 marker 已迁移为 local-only 的 `.leetcode_local_cli/workspace.toml`；内测阶段不兼容旧 Session 和旧 marker。
- HTTP 凭据发送限制为精确 LeetCode CN HTTPS 地址，关闭并拒绝全部重定向，测试使用可注入 transport。
- Session 统一为单次读取、校验与类型化结果；Doctor 不再为正常业务提供前置校验，凭据默认 repr 脱敏。
- 原 `workspace.py` 拆成解法存储、执行 worker 和编辑器集成；底层按职责分包，不保留旧根模块转发。`solve --no-open` 只保存，打开失败警告但保存成功仍退出 0。
- 账号聚合放入用例，HTTP 返回冻结的账号、题目分页和详情模型；业务错误带稳定类别，`test --stdin` 的路径解析失败也输出 JSON。
- 新增 `init <完整路径> --repair`：损坏配置先同目录原字节备份，失败尝试回滚；不支持的版本、站点和语言优先拒绝，不覆盖解法。
- 新增普通 push/PR 的三平台 Python 3.12 CI，固定 Actions SHA，不授予发布权限。
- 源码仓库停止跟踪根目录 `solution.py` 并忽略它，本地解法保留；普通用户仍可自由选择工作区位置。

## 当前优先级

1. **当前版本发布收尾**：核实对应提交的三平台 CI、构建和两种产物安装；整理版本与发布说明；获得发布授权后完成发布和公开安装验证。（当前进度：发布前反馈修复已完成本地门禁与双产物隔离安装验收，待推送并在三平台 CI 复验后，由维护者授权打标签发布与公开安装验证。）
2. **只读查询有限重试**：按操作性质划分重试策略，仅允许只读查询（包含本质为 GraphQL POST 的 `problem_list` / `problem_detail` / `user_status` / `problem_stats` 等）在明确次数和单调时间预算内恢复瞬时故障；初始提交 POST 仍严禁自动重试，判题状态轮询沿用现有限时预算策略。
3. **示例输入回放**：支持当前题目的示例输入复用，沿用现有 worker；明确只报告调用结果，不宣称答案正确。
4. **系统凭据存储**：先确定平台支持、存储不可用时的行为及旧 Session 处置，再单独实现和验收。
5. **查询缓存**：先测量请求次数与耗时，再决定缓存范围、容量和失效规则。

暂缓：**国际站适配器、设计题协议**（等真实需求成立，再调整产品边界）。

低优先级候选：Broken Pipe、合法空分页、Python 小版本范围和依赖审计。

## 已知风险

- Session 已离开工作区，但仍是用户本地状态目录中的明文 JSON。
- 本地 worker 可限制异常和超时，但不是安全沙箱。
- 稳定 Python API 和站点适配器尚未形成。
- HTTP 的全部重定向拒绝策略可能在接口迁移时使命令暂时失败，需要显式更新适配器；这是保护凭据和避免重放提交的取舍。
- 配置修复提供异常回滚和原始字节备份，不提供断电时的跨文件事务或多进程锁。
- 当本机 `uv` 版本（如 `0.13.7`）超出 `pyproject.toml` 中声明的 `uv_build>=0.11.7,<0.12.0` 范围时，直接执行 `uv build --no-sources` 或 sdist 隔离安装会给出后端版本范围警告；使用 `uv build --no-sources --force-pep517` 可验证在声明范围内正常构建，但目前暂不调整构建后端依赖声明，继续作为已知构建警告保留。
- 本次 Windows 验收中，在 Zed 进程运行时有一次切题写入于 `os.replace` 阶段返回 `WinError 5`；旧解法得到保留，随后相同原子替换连续 3 次成功，未形成稳定复现。

详细风险见 [SECURITY_REVIEW](SECURITY_REVIEW.md)。

## 长期方向

核心边界稳定后，再评估国际站、最小 Python API、系统秘密存储和编辑器集成。这些方向不是当前排期，也不授权预先引入数据库、Web、AI 或多语言运行时。

## 最近验证

2026-11-16（UTC），`v0.12.0` 发布前反馈修复与非交互登录兜底：完成 `lc check` 未确认中间态提示、`401` / `403` 与结构化 GraphQL 鉴权/权限分类（不泄露原始响应、初始提交 POST 保持不自动重试）、`lc login` 非 TTY 手动 Cookie 快速失败与 `EOFError` 干净退出，以及 Session / 题目命令文档校准。本地通过 `uv run ruff format --check src tests scripts`（79 个文件）、`uv run ruff check src tests scripts pyproject.toml`、`uv run pyright src tests scripts`（0 errors）、完整 Windows 测试（670 passed、18 skipped，较 `78e62ea` 基线增加 40 项回归与参数化用例）、`uv run lc --version`（`leetcode-local-cli 0.12.0`）与 `--help`，并通过 `uv build --no-sources`、`uv build --no-sources --force-pep517` 及 wheel / sdist 隔离安装 `scripts/smoke_test.py`（`--force-pep517` 构建无后端版本警告；直接 `uv build --no-sources` 与 sdist 隔离安装仍有 `uv 0.13.7` 超出 `uv_build <0.12.0` 范围警告）。推送后由 GitHub Actions `ci.yml` 在三平台复验。

补充真机实测归档（在修复期间由维护者授权本机执行，已按当前源码核对）：
- 已在真实文件、真实 LeetCode CN 接口或真实 worker 上实证：`session.json` 缺失 / 非法 JSON / 结构错误 / 缺 `csrftoken` / 非 UTF-8 均按预期干净退出 1（`submit` 先校验本地解法提交标记，再读 Session）；伪造 Cookie 下 `status`/`profile` 报登录态无效、`get`/`solve` 仍可查询公开题目、真实 `submit` 收到 HTTP `403` 后已准确进入 `FORBIDDEN` 提示（修正之前过期 JWT 响应走通用 HTTP 错误的观察）；真实提交 Wrong Answer（`760128980`）与 `lc submit --wait-timeout 0.5` 超时保留 ID 后经 `lc check 760129019` 复查 Accepted 的恢复链路；不存在大 ID `99999999999` 走 `SubmissionPollingFailed`；死 DevTools 端口 `--devtools-port 19999` 失败后原有 `session.json` 未被破坏（并暴露了无 TTY 下 `getpass` 挂起问题，已在随后提交中修复为快速失败）；真实 `v1` `config.toml` 经 `lc config editor --clear` 升级为 `v2` 并保留有效字段，未配置编辑器时 `solve` 仅警告且退出 0，复原 `zed` 正常；真 worker `ValueError` 返回准确 `error_line` 与 `--verbose` 调用栈，死循环 `--timeout 1` 超时后可重启 worker 继续处理后续输入。注：实测期间跨账号 ID `747241009` 曾看到旧版“提交仍在判题中”（并行改动重叠或全局旧版入口所致），当前仓库 `rendering.py` 已切换为“暂未取得可确认的判题结果……请确认提交 ID 和账号”。
- 真机环境未触发或未重复实测的范围（依赖自动化测试或远端 CI 覆盖）：真实 `submit` 路径上的 HTTP `401` 与 `3xx` 重定向响应、全新 Chrome/Edge 授权弹窗及 180 秒预算完整交互流程、`init --repair` 实机修复执行，以及 Linux / macOS 平台测试（待推送后由 `ci.yml` 覆盖）。

外部真实环境初测反馈归档（对应发布前初始报告）：暴露了 `lc check` 对跨账号 `747241009` 的 `PENDING` 误导文案、过期 Session 下 `show`/`get`/`solve` 与 `status`/`profile` 文档错位、`submit` 缺少 401/403 鉴权分类、只读 GraphQL 查询缺少瞬时重试以及 `uv 0.13.7` 后端版本警告；同时侧面印证了 `--editor` Shell 命令串退出码 2 不执行、无效编辑器保存警告退出 0、`solve` 覆盖普通 `solution.py`、不存在题号 `lc get 99999999` 与空 `solution.py --stdin` 输出 `startup_error` 等设计边界。需特别注明两项环境偏差：初测时浏览器当前登录账号与 `session.json` 保存的用户名不一致（跨账号归属必须以同一份 Cookie 查询到的远端账号为准），且测试脚本通过管道 `$?` 采集到的是 `tail` 而非 `lc` 的退出码，因此该记录**不作为“30 题全部 Accepted”的证据归档**。

2026-11-14（UTC）先前的 `78e62ea` 提交已在 GitHub Actions `ci.yml`（Run `43668890993`）通过 `ubuntu-latest`、`windows-latest` 与 `macos-latest` 三平台 Python 3.12 门禁。

2026-11-14，`v0.12.0` 发布准备：针对提交 `9c7a4f2` 在 Ubuntu/macOS CI（645 passed、1 skipped）中暴露的 2 项 `test_cli.py` 纳秒级 `monotonic()` 严格相等断言失败补齐固定假时钟与 `pytest.approx`，完成 `pyproject.toml` / `uv.lock`（`0.12.0`）、`README.md`、`docs/release-notes/v0.12.0.md` 与路线图同步。本地通过 `uv run ruff format --check src tests scripts`（79 个文件）、`uv run ruff check src tests scripts pyproject.toml`、`uv run pyright src tests scripts`（0 errors）、完整 Windows 测试（630 passed、18 skipped）、`uv run lc --version`（`leetcode-local-cli 0.12.0`）与 `--help`。分别通过 `uv build --no-sources` 与 `uv build --no-sources --force-pep517` 成功构建 `0.12.0` wheel 与 sdist（`--force-pep517` 无后端范围警告；直接 `uv build --no-sources` 与 sdist 隔离安装阶段因本机 `uv 0.13.7` 超出 `uv_build <0.12.0` 声明范围给出版本警告），两种产物均通过 `scripts/smoke_test.py` 隔离安装验收。未创建标签或发布，未修改全局工具安装，未访问真实账号、启动真实浏览器或本地编辑器；推送后等待三平台 `ci.yml` 复验。

2026-11-14，以上四项正确性修复（含 f-string 嵌套/未闭合处理与浏览器窗口打开后剩余预算重算）通过 `uv run ruff format --check src tests scripts`（79 个文件）、`uv run ruff check src tests scripts pyproject.toml`、`uv run pyright src tests scripts`（0 errors）以及完整 Windows 测试（630 passed、18 skipped），比上轮增加 52 项回归测试与参数化用例。18 项跳过仍为本机符号链接权限限制与 POSIX/Bash 平台限定；登录预算与网络校验均采用假时钟、模拟 WebSocket 与注入 HTTP transport 完成，未启动真实浏览器、未访问真实账号、未执行远程提交或启动真实编辑器，未修改全局安装且未创建 Git 提交或标签。

2026-09-07，发布前收尾补齐三平台产物门禁，通过发布/仓库卫生定向测试（26 passed、1 skipped）、Ruff format/lint、Pyright（0 errors）及完整 Windows 测试（578 passed、18 skipped）。使用 `uv build --no-sources --force-pep517` 按声明范围内的后端成功构建，未出现版本范围警告；生成的 wheel/sdist 分别通过隔离安装 smoke test。sdist 安装阶段仍走本机 uv 内置快路径并提示版本范围警告，不能将单独的 PEP 517 构建通过描述为全链路告警已消除。依赖与全局工具未修改；远端工作流、真实编辑器窗口仍未验收，未提交、推送或发布。

2026-09-07，以上四项审查修复通过 Ruff format（79 个文件）、Ruff lint、Pyright（0 errors）及完整 Windows 测试（574 passed、18 skipped），比上轮增加 57 项回归检查。覆盖配置版本独立与显式升级、拒绝未来版本和旧版本写入、控制字符往返与失败保留原件、普通/延迟节点注解及普通字符串、真实 worker 超时后加载失败与再次恢复，以及交互/JSON 的行号和可选调用栈。

通过 `uv build --no-sources`、`uv run lc --version` / `--help` 和 wheel/sdist 隔离安装 smoke test。18 项跳过仍为 Windows 符号链接权限与 POSIX/Bash 平台限定；未执行远端三平台 CI。构建仍提示 uv 0.12.5 与 `uv_build <0.12.0` 的声明范围不一致，未改依赖。本轮测试仅使用临时配置与解法，没有访问真实账号、改写本机用户配置/Session 或打开编辑器；版本仍为 0.11.0，未提交、推送或发布。

2026-09-06，编辑器设置与本地节点能力通过 Ruff format（79 个文件）、Ruff lint、Pyright（0 errors）及完整 Windows 测试（517 passed、18 skipped）。通过 `uv build --no-sources`、版本/帮助入口和 wheel/sdist 隔离安装 smoke test；验证新命令、编辑器设置在初始化前后保留、包内节点定义及树数组输入输出。18 项跳过为本机符号链接权限限制和 POSIX/Bash 平台限定；本轮未执行 Linux/macOS CI。构建仍有 uv 0.12.5 与声明的 `uv_build <0.12.0` 版本范围警告，未变更依赖。

同日经维护者明确授权，复用现有账号和源码工作区，`status`、`profile`、`show`、`get` 成功；隔离用户配置路径但保留原 Session 位置，`profile` 成功而 `test --stdin` 正确返回工作区缺失，证明登录态不依赖工作区初始化。第 2、94、1 题均用真实模板切题，分别验证 3、4、4 组本地输入，结果符合预期。第 1 题仅提交一次，Submission ID `747241009` 返回 Accepted（65/65），再执行 `check` 同样 Accepted。

原有空 `solution.py` 已按原始字节恢复，Session 未重写或输出；用户编辑器设置为 `zed`。未调用电脑控制、重新登录或启动真实编辑器，编辑器启动仅以替身及无界面的参数记录进程验收。链表和树题仅本地运行，未额外远端提交。以上不代表重新登录流程、编辑器窗口或所有节点题型已完成实机验收。

2026-09-05，分层重构和安全边界修复通过 Ruff format、Ruff lint、Pyright（0 errors）和 Windows 测试（443 passed、18 skipped），并通过 `uv build --no-sources`、版本/帮助入口及 wheel/sdist 隔离安装 smoke test。产物验收包含临时工作区初始化、无工作区 JSON 错误、本地 worker 的实际调用与返回值检查。

18 项跳过包括本机缺少符号链接权限的 11 项及仅适用 POSIX/Bash 的 7 项；Windows junction/reparse point 检查已运行。三平台 CI 尚未远端执行，真实浏览器、登录和远端提交未验收，本轮未读取真实 Cookie。构建时本机 uv 0.12.5 对 `uv_build <0.12.0` 声明给出版本警告，但构建和隔离产物验收成功；未变更依赖或发布版本。

2026-09-04，用户状态/工作区路径拆分、初始化前命令和新 marker 通过完整 Ruff format、Ruff lint、Pyright 和 Windows 测试（346 passed、14 skipped），并通过 `uv build --no-sources`、`lc --version`、`lc --help` 与隔离的无工作区 `lc profile` Smoke Test。自动化验证未读取真实 Cookie、执行真实登录或远程提交。

2026-09-04，未发布的浏览器登录提示和文档变更通过完整 Ruff format、Ruff lint、Pyright 和 Windows 测试（335 passed、13 skipped）。自动化验证未执行真实 Cookie 读取或远程提交。

`v0.10.1` 通过 Ruff format、Ruff lint、Pyright、Windows 完整测试（333 passed、13 skipped）、wheel/sdist 构建及两种产物的隔离安装 smoke test。首次 `v0.10.0` 标签工作流因 CLI 彩色输出测试直接匹配 ANSI 文本而停止，未进入 PyPI 和 GitHub Release；测试改为去色后验证公开文案。2026-08-09 使用维护者明确授权的现有登录态，对随机选取的 10 道免费 Easy 题完成真实提交，10 次均为 Accepted；对应的 10 个 Submission ID 再次执行 `lc check` 均返回 0。测试期间未输出 Cookie，原有空 `solution.py` 已恢复。

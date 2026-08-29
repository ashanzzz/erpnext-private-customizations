# ERPNext 16 自定义工作台与 UI/UX 合并核验审计报告

审计日期：2026-08-28  
报告性质：只读源码、元数据、既有证据与有限连通性复核  
适用应用：`ashan_cn_procurement`  
报告状态：合并定稿。运行时业务链仍未充分验证

## 一、执行结论

本报告对三份既有审计报告逐条比对，并重新核对当前源码、Page/DocType metadata、既有自动化日志、既有截图和可执行的只读检查。

三份旧报告都包含有效内容，但没有任何一份可单独作为最终审计结论：

- 仓库内的全局报告保留了真实截图目录和部分正确的 UI 统计，但把失败的第一轮路由检查写成“全部通过”。
- Telegram 报告准确指出若干视觉和文案问题，但其“27 个页面全部实测”“所有写入 RPC 都使用 POST”等结论与当前源码直接冲突。其证据目录在当前主机不存在。
- 原 Codex 报告对权限、公司范围和单据生命周期的审查更深入，但把不同类型的表面相加为“91 个 UI 表面”，漏计了 3 个 DocType 客户端脚本，也没有使用后来发现的历史截图证据。

合并核验后的标准库存不再使用一个容易重复计数的“总表面数”。当前事实是：

| 类型 | 当前数量 | 核验方法 |
|---|---:|---|
| 自定义 Desk Page | 21 | Page JSON 与 Page JS 一一对应 |
| Workspace | 7 | Workspace JSON |
| Script Report | 15 | Report JSON |
| 自定义 DocType | 51 | DocType JSON |
| 带客户端脚本的自定义 DocType | 36 | 同名 DocType JS |
| hooks 注册的标准表单/列表脚本 | 8 | `hooks.py` |
| 共享 UI 资源 | 7 | hooks 与 public 目录 |

本次确认 4 项 P0 代码风险、8 项 P1 产品或验证风险、9 项 P2/P3 体验与治理问题。最严重问题位于油卡、物业月结和税局发票服务端。它们可能破坏公司边界、标准单据生命周期、余额守恒或原始凭证保全。

历史证据中存在 66 张按 22 个路由和 3 个视口命名的截图。它们可证明页面曾经渲染，但不能证明权限、业务状态、网络、Console、草稿恢复或路由回访通过。部分截图包含员工、薪酬、账号和业务单据内容。本报告不复制、不链接这些图片。

当前只读浏览器复核仍在目标站点加载阶段超时。因此，本报告没有把任何写入流程、权限负向场景或财务结果标记为本次已实机通过。

## 二、输入报告与证据可信度

### 2.1 输入报告指纹

| 编号 | 文件 | SHA-256 | 主要价值 | 主要限制 |
|---|---|---|---|---|
| R-A | `ERPNext16_UI_UX_Global_Audit_Report.md` | `972D9620FA2C84DB62CCDE5BFEA58D689FD3CD2FAC1C321D97A39A9C68B78AD7` | 给出 22 路由、三视口和截图目录 | 把失败日志写成全部通过，报告内含未脱敏账号信息 |
| R-B | `ERPNext16_UI_UX_Global_Audit_Report_20260828.md` | `0B8CA0A6650693B482A1C1FF41092694B7EDFC9AA364807E6A1BC68DF64DF8A6` | 识别电汇文案、紫色按钮、斜杠标题、视觉密度问题 | 路由数量和 RPC 结论与源码冲突，证据目录当前不可访问 |
| R-C | `ERPNext16_UI_UX_Audit_Report_2026-08-28.md` | `B149F0998FBF602D5E58D726DAD86D11D713EB990EF5DAC7490622C0B94A07D4` | 识别权限、公司范围、油卡生命周期、凭证删除和 XSS 风险 | UI 表面总数口径不准确，运行时证据不足 |

### 2.2 证据等级

| 等级 | 定义 | 本报告用途 |
|---|---|---|
| E1 | 本次可重复的运行时证据，定位到角色、公司、视口和请求 | 本次为 0 项 |
| E2 | 可读取的历史日志或截图，具备文件指纹 | 只证明当时页面外观或日志内容 |
| E3 | 当前源码、metadata、hooks 或只读静态检查 | 支持“代码缺陷”或“代码风险”结论 |
| E4 | 报告中的文字陈述，没有可用原始证据 | 只作线索，不作通过依据 |

### 2.3 历史自动化证据核验

历史证据目录包含 88 张 PNG 和 2 个 JSON。

第一份 JSON `spa_audit_summary.json` 记录 22 个路由。除 Home 外，21 个自定义路由全部使用下划线路由。每项均显示首页标题、0 个表格、0 行数据和一个 404。其返回页检查结果是 `isMounted=false`。这次执行不能支持任何页面通过结论。

第二份 JSON `accurate_spa_summary.json` 使用正确的连字符路由，并生成了 22×3 张截图。但其 DOM 统计没有限制在当前 wrapper：表格数从第一个页面的 1 累积到最后页面的 34，行数从 3 累积到 355，薪酬页面还保留上一页面标题。该日志可作为“页面曾渲染”的历史证据，不能作为路由隔离、无白屏、网络健康或性能通过证据。

第二份 JSON 的 `errors=[]` 只表示该脚本没有收集到其定义的错误。它没有保存完整 Network 请求清单、响应状态、请求取消原因或角色矩阵。因此，旧报告中的“0 个非预期网络失败”没有足够证据。

## 三、完整覆盖清单

### 3.1 自定义 Desk Page

状态说明：代码审查表示当前源码和 metadata 已核对。历史渲染表示存在三视口截图，但截图证据没有达到 E1。当前实机表示本次浏览器复核结果。

| 模块 / 页面 | Desk 路由 | 主要源码 | 关联对象或服务 | Page metadata 角色 | 写入 | 代码审查 | 历史渲染 | 当前实机 |
|---|---|---|---|---|---:|---|---|---|
| 员工薪酬与人事档案台 | `/desk/employee-salary-workbench` | `page/employee_salary_workbench/` | Salary Profile、employee salary service | System Manager | 是 | 已完成 | 有 | 阻塞 |
| 环保管理 | `/desk/environmental-management` | `page/environmental_management/` | Environmental Compliance Item | System Manager、Purchase Manager、Compliance Manager/Operator | 是 | 已完成 | 有 | 阻塞 |
| 吉众人事薪酬工作台 | `/desk/jizhong-hr-salary-workbench` | `page/jizhong_hr_salary_workbench/` | Payroll Settlement | System Manager、HR/Accounts Manager 或 User | 是 | 已完成 | 有 | 阻塞 |
| 房租物业月结 | `/desk/lease-settlement-workbench` | `page/lease_settlement_workbench/` | Property Lease、property settlement service | System Manager、Administrator、Accounts Manager/User | 是 | 已完成 | 有 | 阻塞 |
| 收货入库 | `/desk/material-receipt-workbench` | `page/material_receipt_workbench/` | Purchase Receipt、shared procurement workbench | System Manager、Stock Manager/User | 是 | 已完成 | 有 | 阻塞 |
| 物料申请 | `/desk/material-request-workbench` | `page/material_request_workbench/` | Material Request、shared procurement workbench | System Manager、Purchase/Stock Manager 或 User | 是 | 已完成 | 有 | 阻塞 |
| 工作餐费月结 | `/desk/meal-settlement-workbench` | `page/meal_settlement_workbench/` | Monthly Meal Settlement | System Manager、HR Manager/User、Accounts Manager | 是 | 已完成 | 有 | 阻塞 |
| 月度核定全景管理中枢 | `/desk/monthly-closing-center` | `page/monthly_closing_center/` | 各模块封账接口 | 多模块 Manager/Operator 及遗留通用角色 | 是 | 已完成 | 有 | 阻塞 |
| 月结补录 | `/desk/monthly-settlement-picker` | `page/monthly_settlement_picker/` | Monthly Settlement Service | System Manager、Purchase/Stock/Accounts Manager 或 User | 是 | 已完成 | 有 | 阻塞 |
| 油卡综合台账 | `/desk/oil-card-ledger` | `page/oil_card_ledger/` | Oil Card、Recharge、Refuel Log | Oil Card Manager/Operator、System Manager 及遗留通用角色 | 是 | 已完成 | 有 | 阻塞 |
| 人事与薪酬月结 | `/desk/payroll-settlement-workbench` | `page/payroll_settlement_workbench/` | Payroll Settlement | System Manager、HR Manager、Accounts Manager | 是 | 已完成 | 有 | 阻塞 |
| 采购执行 | `/desk/procurement-execution-workbench` | `page/procurement_execution_workbench/` | Purchase Order、shared procurement workbench | System Manager、Purchase/Accounts Manager 或 User | 是 | 已完成 | 有 | 阻塞 |
| 水电费月结 | `/desk/property-settlement-workbench` | `page/property_settlement_workbench/` | Property Monthly Settlement | Property Manager/Operator、System Manager、Accounts Manager/User | 是 | 已完成 | 有 | 阻塞 |
| 祺富人事薪酬工作台 | `/desk/qifu-hr-salary-workbench` | `page/qifu_hr_salary_workbench/` | Payroll services | System Manager、HR/Accounts Manager 或 User | 是 | 已完成 | 有 | 阻塞 |
| 报销申请 | `/desk/reimbursement-picker` | `page/reimbursement_picker/` | Reimbursement Request | System Manager、Purchase/Accounts Manager 或 User | 是 | 已完成 | 有 | 阻塞 |
| 特种设备管理 | `/desk/special-equipment-center` | `page/special_equipment_center/` | Special Equipment、Inspection | System Manager、Compliance Manager/Operator | 是 | 已完成 | 有 | 阻塞 |
| 材料出库 | `/desk/stock-issue-workbench` | `page/stock_issue_workbench/` | Stock Entry、Bin | System Manager、Stock/Purchase/Accounts Manager 或 User | 是 | 已完成 | 有 | 阻塞 |
| 库存收发流水台账 | `/desk/stock-ledger-workbench` | `page/stock_ledger_workbench/` | Stock Ledger Entry、Stock Entry | System Manager、Stock/Accounts Manager 或 User | 是 | 已完成 | 有 | 阻塞 |
| 税局发票 | `/desk/tax-invoice-center` | `page/tax_invoice_center/` | Tax Invoice、File、cleanup service | System Manager、Accounts Manager/User | 是 | 已完成 | 有 | 阻塞 |
| 高速费月度台账 | `/desk/vehicle-toll-ledger` | `page/vehicle_toll_ledger/` | Vehicle Toll 系列对象 | Oil Card Manager/Operator、System Manager 及遗留通用角色 | 是 | 已完成 | 有 | 阻塞 |
| 自办电汇 | `/desk/wire-transfer-picker` | `page/wire_transfer_picker/` | Purchase Invoice、Stock Entry、Payment Entry | System Manager、Purchase/Stock/Accounts Manager 或 User | 是 | 已完成 | 有 | 阻塞 |

### 3.2 Workspace、Report、DocType 和共享能力

Workspace 共 7 项：Accounting and Finance、Company Compliance Center、My Business、Procurement Management、Property and Lease、Stock and Inventory、Vehicle Fuel Hub。它们均为 public metadata。公开 Workspace 只说明入口可见，不说明其中数据可读。

Script Report 共 15 项：Company Compliance Overview、Company Compliance Pending Purchase、Compliance Expiry Trend、Oil Card Balance Reconciliation、Oil Card Card Summary、Oil Card Monthly Ledger、Oil Card Operating Summary、Oil Card Recharge Ledger、Oil Supplier Invoice Summary、Property Settlement History、Reimbursement Payment Status、Unpaid Reimbursement List、Vehicle Fuel Cost Summary、Vehicle Monthly Fuel Trend、Vehicle Refuel Ledger。

自定义 DocType 共 51 项。其中 36 项有同名客户端脚本。主要对象包括薪酬、餐费、节假日、油卡、物业、报销、权限组、特种设备、税局发票、水电表和车辆高速费。完整名称以 `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/doctype/` 下 51 个 JSON 为准。

`hooks.py` 另注册 3 个标准表单脚本：Purchase Invoice、Reimbursement Request、Vehicle。它还注册 5 个标准列表脚本：Material Request、Purchase Order、Purchase Receipt、Purchase Invoice、Reimbursement Request。

共享 UI 资源共 7 项：`ashan_ui_kit.css`、`ashan_ui_kit.js`、`ashan_cn_procurement.css`、`ashan_work_context.js`、`ashan_cn_sidebar_v2.js`、`doc_details_list.js`、`procurement_workbench.js`。

## 四、总体健康度评分卡

| 维度 | 评级 | 结论依据 |
|---|---|---|
| 业务与财务严谨性 | D | 油卡草稿进入余额、物业封账接口和原始发票附件清理均存在高风险代码路径。库存台账四柱结构存在，但没有运行数据复算。 |
| 权限与代码架构 | D | Page、DocPerm 和服务端角色模型漂移。至少 38 个名称明确的写入入口使用默认 whitelist。多处 `ignore_permissions` 前缺少最终资源鉴权。 |
| UI 设计系统一致性 | C | 样式门禁通过，但仍有 1,572 个内联样式。大量页面含装饰性图符、斜杠标题、专页颜色和重复组件。 |
| 人机工程与操作效率 | C | 原位办理能力较强。电汇高风险批量动作的文案不够准确。窄屏首屏被 KPI、说明和任务卡占用。 |
| SPA 稳定性与性能 | 未充分验证 | 11 个页面缺少 `on_page_show`。共享采购工作台有全局事件解绑风险。历史自动化使用了错误的全局 DOM 统计。 |
| 响应式与可访问性 | 未充分验证 | 66 张历史截图证明页面曾在三视口渲染，但没有焦点、键盘、滚动同步、读屏或当前版本复测证据。 |

## 五、确认的正向实现

这些条目只表示代码结构达标。它们不表示运行结果已通过。

| 模块 | 代码层达标项 | 证据 |
|---|---|---|
| 库存流水台账 | 明确计算期初、本期入库、本期出库和期末。前端显示四组列及合计行。 | `stock_ledger_workbench.py:168-386,612-755`；`stock_ledger_workbench.js:801-877,983-1074` |
| 油卡台账 | 页面显示期初、充值、消费、期末和逐笔余额。 | `oil_card_ledger.py:352-472`；`oil_card_ledger.js:1679-1781` |
| 报销服务 | 主要创建和草稿删除接口已使用 POST，并检查公司和草稿状态。 | `reimbursement_picker_service.py:891,981-988` |
| 月结补录 | 主创建入口已使用 POST，并检查公司。 | `monthly_settlement_service.py:391-400` |
| 自办电汇 | 主建单和批量出库入口使用 POST，并重新加载 Purchase Invoice 后检查公司。 | `wire_transfer_service.py:664-687,1200-1215` |
| 库存快捷出库 | 主创建入口已使用 POST，并检查公司。 | `stock_issue_workbench.py:534-551`；`stock_ledger_workbench.py:762` |
| 环保写入 | 已检查的写入入口使用 POST，并调用公司权限。 | `environmental_management.py:148-284` |
| 弹窗防误触 | 报销、月结补录和电汇的若干关键 Dialog 已设置静态背景。 | `reimbursement_picker.js:735,770,802`；`monthly_settlement_picker.js:758,1192`；`wire_transfer_picker.js:948,1014,1117,1527` |

油卡结构虽然显示四柱，但 OIL-002 使其数据集合包含草稿。因此，不能把油卡结果判定为财务通过。

## 六、缺陷总表

| 编号 | 级别 | 模块 | 结论类型 | 核心问题 |
|---|---|---|---|---|
| OIL-001 | P0 | 油卡 | E3 代码缺陷 | 删除目标未与受权油卡、公司和期间绑定 |
| OIL-002 | P0 | 油卡 | E3 代码缺陷 | 可提交记录仅 insert，草稿立即进入余额 |
| PROP-001 | P0 | 物业 | E3 代码缺陷 | 保存、核定、解锁和账单读取未见服务端权限收口 |
| TAX-001 | P0 | 税局发票 | E3 代码缺陷 | 上传、状态变更、设置和原件删除链缺少最终授权 |
| AUTH-001 | P1 | 跨模块 | E3 配置缺陷 | Page、DocPerm、RPC 与双角色模型漂移 |
| RPC-001 | P1 | 跨模块 | E3 代码缺陷 | 至少 38 个明确写入入口未限制 POST |
| INV-001 | P1 | 库存 | E3 代码缺陷 | 仓库可用量查询未从真实仓库反向校验公司 |
| XSS-001 | P1 | 库存 | E3 代码缺陷 | 业务字段直接进入 HTML 和 data 属性 |
| COM-001 | P1 | 特种设备 | E3 代码缺陷 | 快捷建档和检验接口未见模块/公司鉴权 |
| COM-002 | P1 | 环保 | E3 代码风险 | 默认读取分支可返回全公司集合 |
| TEST-001 | P1 | 验证工具 | E3 代码缺陷 | 名为集成测试的脚本会创建并提交真实采购发票 |
| WIRE-001 | P1 | 自办电汇 | E2+E3 缺陷 | “全部出库”会提交库存和整算单，文案不足以表达影响 |
| SPA-001 | P2 | 跨页面 | E3 代码风险 | 11 个数据页面没有 `on_page_show` |
| SPA-002 | P2 | 采购共享工作台 | E3 代码风险 | document 事件无对应解绑 |
| DRAFT-001 | P2 | 报销/月结/电汇 | E3 代码风险 | 未发现跨关闭和重开可恢复的完整草稿引擎 |
| UI-001 | P2 | 跨模块 | E3 已执行 | 1,572 个存量内联样式 |
| UI-002 | P2 | 跨模块 | E2+E3 风险 | 15 个页面含 46 个字面量 select，未按控制类型治理 |
| UI-003 | P2 | 薪酬/税票/电汇 | E2 视觉缺陷 | 900px 视口中首屏被头部和 KPI 占用 |
| UI-004 | P2 | 薪酬 | E2 视觉缺陷 | 部分金额缺少千分位 |
| UI-005 | P2 | 自办电汇 | E2+E3 视觉缺陷 | 主按钮使用专页紫色，行操作密集 |
| PAY-001 | P2 | 薪酬 | E3 代码缺陷 | 固定公司和历史期间默认值进入服务参数 |
| COPY-001 | P3 | 跨模块 | E2+E3 文案缺陷 | 装饰性图符和斜杠拼接标题广泛存在 |
| AUDIT-001 | P1 | 审计证据 | E2 证据缺陷 | 历史截图含敏感信息，旧日志未限制当前 wrapper |

## 七、P0 与 P1 详细发现

### OIL-001：删除目标未绑定真实油卡、公司和期间

- 严重级别：P0。
- 页面与路由：油卡综合台账，`/desk/oil-card-ledger`。
- 角色、公司、视口：Oil Card Manager；测试公司 A/B；接口级，视口不适用。
- 复现步骤：在隔离测试站创建两张测试油卡。用卡 A 的授权参数调用删除接口，但传入卡 B 的流水名称。
- 预期结果：服务端加载目标流水，从目标流水取得油卡、公司和日期，再完成授权与锁账校验。
- 实际结果：本次未写数据。源码先对请求参数 `oil_card` 授权，再按 `doc_type/name` 加载并删除目标。没有比较 `doc.oil_card`、目标公司和目标日期。
- 用户与业务影响：用户可能删除另一张卡的流水。系统随后只重算请求中的卡，导致被删卡余额不一致。
- 运行证据：无。本项是代码缺陷。
- 源码位置：`page/oil_card_ledger/oil_card_ledger.py:832-891`。
- 根因：授权对象和变更对象不是同一个服务端 Document。
- 修复建议：先加载目标 Document。只从目标 Document 推导油卡、公司和月份。对请求参数只作一致性检查。删除和真实卡余额重算放在同一事务。
- 修复后验证：双卡、双公司、锁定月、管理员/操作员/无权角色和余额四柱测试。
- 置信度：高。

### OIL-002：可提交业务在草稿状态进入正式余额

- 严重级别：P0。
- 页面与路由：油卡综合台账，`/desk/oil-card-ledger`。
- 角色、公司、视口：Oil Card Operator；隔离测试公司；接口级。
- 复现步骤：通过快捷充值或快捷加油创建测试记录。检查 `docstatus`、自定义状态和油卡余额。
- 预期结果：可提交 DocType 只有 `docstatus=1` 的记录进入正式台账和余额。
- 实际结果：本次未写数据。两个 DocType 都是 `is_submittable=1`。快捷接口只调用 `doc.insert()`，却写入文本 `status="Submitted"`。余额查询使用 `docstatus != 2`，所以草稿立即入账。
- 用户与业务影响：草稿、提交和取消语义失真。余额、封账和报表可能包含未经提交的记录。
- 运行证据：无。本项是代码缺陷。
- 源码位置：`oil_card_recharge.json:16`、`oil_card_refuel_log.json:16`、`oil_card_ledger.py:352-454,568-708`。
- 根因：自定义文本状态替代 Frappe 标准生命周期。
- 修复建议：即时过账模式必须执行 `insert()` 后 `submit()`。草稿模式必须把余额查询改为 `docstatus=1`。删除不必要的请求内手工 commit。
- 修复后验证：草稿、提交、取消、重复提交、异常回滚和月度锁定测试。
- 置信度：高。

### PROP-001：物业月结和解锁接口未见最终授权

- 严重级别：P0。
- 页面与路由：`/desk/property-settlement-workbench`、`/desk/lease-settlement-workbench`。
- 角色、公司、视口：无 Property 角色的已认证用户；公司 A/B；接口级。
- 复现步骤：在测试站直接调用保存、核定、退回草稿、租约发票更新和账单读取 RPC。
- 预期结果：每个写入入口使用 POST。服务端检查模块动作、真实公司、Document 状态和解锁理由。
- 实际结果：本次未调用。Page wrapper 使用默认 whitelist。服务层以 `ignore_permissions` 保存租约和结算，未见 `assert_module_access`、`assert_company_access` 或 `has_permission`。
- 用户与业务影响：无权写入、跨公司读取、封账被无理由退回和租约对账被改变。
- 运行证据：无。本项是代码缺陷。
- 源码位置：`property_settlement_workbench.py:17-45,119`、`lease_settlement_workbench.py:26-66`、`services/property_settlement.py:161-195,901-995`。
- 根因：服务层把页面调用视为可信调用。
- 修复建议：所有写入改为 POST。服务层集中检查 Property Manager/Operator 动作、真实公司、状态和解锁审计。
- 修复后验证：角色×公司×状态矩阵。直接 RPC 与页面调用必须得到相同授权结果。
- 置信度：高。

### TAX-001：税局发票原件和状态接口缺少最终授权

- 严重级别：P0。
- 页面与路由：税局发票，`/desk/tax-invoice-center`。
- 角色、公司、视口：Tax Invoice Manager/Operator、普通用户；多公司；接口级。
- 复现步骤：在隔离测试站分别直调上传、放弃、恢复、重匹配、删除 PDF、设置保存和立即清理接口。
- 预期结果：接口使用 POST。服务端检查模块角色、真实发票公司、状态和凭证留存规则。
- 实际结果：本次未调用。多个入口使用默认 whitelist。上传直接保存私有 File 和导入批次。删除接口进入清理服务后物理删除 File，并以 `ignore_permissions` 保存发票。设置和状态变更也未见同层授权。
- 用户与业务影响：原始凭证可能被无权删除。发票状态、导入任务和清理策略可能被无权改变。
- 运行证据：无。本项是代码缺陷。
- 源码位置：`tax_invoice_center.py:262-318,358-465`、`services/tax_invoice_cleanup.py:5-35`。
- 根因：敏感文件和配置操作依赖前端入口，没有在最终动作建立权限边界。
- 修复建议：上传、状态、配置和清理分别映射到 Tax Invoice 角色动作。全部使用 POST。原件采用归档或受控保留，不用普通业务接口物理删除。
- 修复后验证：角色、公司、封账、重复附件、保留期限和失败回滚测试。
- 置信度：高。

### AUTH-001：模块双角色模型与 metadata 漂移

- 严重级别：P1。
- 页面与路由：薪酬、油卡、合规、物业、税局发票及月度中枢。
- 角色、公司、视口：metadata 审查；视口不适用。
- 复现步骤：在测试站建立模块 Manager、Operator、Accounts、Purchase、Stock、HR 和无关用户。逐项验证 Page、DocType 和 RPC。
- 预期结果：自定义模块只保留规定的 Manager/Operator 业务角色。平台管理员除外。
- 实际结果：当前 `MODULE_ACCESS_MODEL` 已定义双角色，但 Page JSON 和 DocPerm 仍授予多个通用 Accounts、Purchase、Stock 或 HR 角色。
- 用户与业务影响：入口、表单和服务端的权限结果不一致。最小权限无法成立。
- 运行证据：无。本项是配置缺陷。
- 源码位置：`services/authorization_service.py`、油卡/物业/税票/薪酬 Page JSON 与相关 DocType JSON 的 permissions。
- 根因：新授权服务没有同步清理历史 metadata。
- 修复建议：业务负责人先确认动作矩阵。随后统一 Page.roles、DocPerm 和 RPC。
- 修复后验证：角色×公司×页面×DocType×RPC 自动化矩阵。
- 置信度：高。

### RPC-001：至少 38 个写入入口未限制 POST

- 严重级别：P1。
- 页面与路由：油卡、物业、税票、特种设备、车辆高速费、餐费、节假日和报销旧 API。
- 角色、公司、视口：接口级。
- 复现步骤：在隔离测试站对每个写入方法分别发出 GET 和 POST 请求。
- 预期结果：写入、删除、上传、封账、解锁、审批和导入只接受 POST。
- 实际结果：本次未调用。保守扫描只统计名称明确表示写入且使用默认 `@frappe.whitelist()` 的函数，已得到至少 38 项。旧报告的 25 项已过时。“所有 RPC 均 POST”的结论错误。
- 用户与业务影响：扩大误调用和请求方法风险。也违反项目 API 规则。
- 运行证据：无。本项是代码缺陷。
- 源码位置：`oil_card_ledger.py:167-833`、`tax_invoice_center.py:262-465`、`special_equipment_center.py:141-247`、`vehicle_toll_ledger.py:199-473`、物业与餐费服务等。
- 根因：读写 API 没有统一门禁。
- 修复建议：建立 AST 门禁。写入函数必须显式 `methods=["POST"]`。服务端仍需独立权限检查。
- 修复后验证：HTTP 方法、CSRF、权限和幂等测试。
- 置信度：高。38 是保守下限，不是全部 whitelist 数量。

### INV-001：库存查询未从真实仓库验证公司

- 严重级别：P1。
- 页面与路由：材料出库，`/desk/stock-issue-workbench`。
- 角色、公司、视口：仅有公司 A 权限的库存用户；公司 A/B；接口级。
- 复现步骤：传 `company=A`，但传入公司 B 的 warehouse。
- 预期结果：服务端加载 Warehouse，并验证 `warehouse.company` 与受权公司一致。
- 实际结果：本次未调用。函数只检查请求中的 company。Bin 查询只按 warehouse 过滤，未连接 Warehouse.company。
- 用户与业务影响：可能读取其他公司的库存可用量。
- 运行证据：无。本项是代码缺陷。
- 源码位置：`stock_issue_workbench.py:441-480`。
- 根因：授权绑定请求参数，不绑定真实资源。
- 修复建议：先加载 Warehouse，再对真实公司授权。查询同时增加公司约束。
- 修复后验证：双公司仓库正负向测试。
- 置信度：高。

### XSS-001：材料出库业务字段直接拼入 HTML

- 严重级别：P1。
- 页面与路由：材料出库，`/desk/stock-issue-workbench`。
- 角色、公司、视口：可录备注或维护物料文本的测试用户；隔离测试公司；1366×768。
- 复现步骤：只在隔离记录写入 HTML 特殊字符。让另一测试用户打开列表、建议浮层和详情。
- 预期结果：文本使用 `textContent` 或统一转义。data 属性使用属性编码。
- 实际结果：本次未写测试载荷。源码直接插入用途、备注、物料名称和描述。该文件未见统一 escape helper。
- 用户与业务影响：受控业务字段可能形成存储型 XSS。
- 运行证据：无。本项是代码缺陷。
- 源码位置：`stock_issue_workbench.js:447-451,560-569,1027,1097-1106,1435-1436`。
- 根因：字符串模板承担不可信数据渲染。
- 修复建议：使用 DOM 文本 API 或可靠转义。覆盖文本和属性上下文。
- 修复后验证：隔离环境 XSS 字符集回归。检查 Console 和 DOM。
- 置信度：高。

### COM-001：特种设备快捷写入未见模块和公司鉴权

- 严重级别：P1。
- 页面与路由：特种设备，`/desk/special-equipment-center`。
- 角色、公司、视口：普通 Desk 用户、Compliance Operator/Manager；接口级。
- 复现步骤：在测试站直调快速建档、检验和年检方法。
- 预期结果：POST，并检查 Compliance 动作、公司和关联设备状态。
- 实际结果：本次未调用。三个入口使用默认 whitelist，并以 `ignore_permissions` 插入。文件内未见模块/公司断言。
- 用户与业务影响：合规记录可能被无权创建或改变。
- 运行证据：无。本项是代码缺陷。
- 源码位置：`special_equipment_center.py:141-247`。
- 根因：快捷 UI 入口直接承担最终写入。
- 修复建议：统一进入合规服务的受权 POST 方法。
- 修复后验证：三角色、双公司和设备状态矩阵。
- 置信度：高。

### COM-002：环保默认读取没有公司安全范围

- 严重级别：P1。
- 页面与路由：环保管理，`/desk/environmental-management`。
- 角色、公司、视口：仅有公司 A 权限的用户；公司 A/B；接口级。
- 复现步骤：不传 company、传公司 A、传公司 B，比较返回集合。
- 预期结果：默认结果从用户受权公司集合开始过滤。
- 实际结果：本次未调用。只有显式传 company 才检查公司。默认分支读取全量合规项，并返回全公司列表。
- 用户与业务影响：可能暴露其他公司的合规状态和期限。
- 运行证据：无。本项是代码风险。
- 源码位置：`environmental_management.py:16-33,127`。
- 根因：company 被当成可选筛选条件，不是安全边界。
- 修复建议：从服务端 allowed companies 构造强制过滤。
- 修复后验证：双公司和四角色读取矩阵。
- 置信度：中高。

### TEST-001：集成测试脚本会写入真实业务账

- 严重级别：P1。
- 页面与路由：验证工具，不适用 Desk 路由。
- 角色、公司、视口：脚本从环境读取管理员账号，并自动选第一家公司、供应商和物料。
- 复现步骤：不应在生产或未隔离站点执行。静态阅读即可确认。
- 预期结果：只读审计脚本不写业务数据。写入测试必须要求明确测试站和测试公司。
- 实际结果：`test_china_tax_integration.py` 登录站点，创建 Purchase Invoice，随后把 `docstatus` 改为 1，并读取 GL Entry。脚本没有清理逻辑。它还使用项目已禁止的新写入字段名。
- 用户与业务影响：误运行会产生采购发票和总账数据，污染真实公司。
- 运行证据：本次未运行该脚本。
- 源码位置：`test_china_tax_integration.py:18-111`。
- 根因：现场验收脚本没有测试站硬拦截和数据回收边界。
- 修复建议：要求显式 `TEST_SITE=1` 和测试公司。使用 fixture。把业务写入移到可回滚测试事务。
- 修复后验证：生产地址硬拒绝。测试结束后无残留 Purchase Invoice 或 GL Entry。
- 置信度：高。

### WIRE-001：高影响批量动作使用“全部出库”文案

- 严重级别：P1。
- 页面与路由：自办电汇，`/desk/wire-transfer-picker`。
- 角色、公司、视口：Purchase/Accounts 获权用户；历史 1920×1080 与 900px 截图。
- 复现步骤：进入页面，选择采购发票，点击“全部出库”，查看确认文案和服务端结果。
- 预期结果：按钮直接说明它会生成并提交领料出库单和整算单。
- 实际结果：历史截图和源码均显示“全部出库”。服务端对每个发票创建并提交 Stock Entry 和 Reimbursement Request。
- 用户与业务影响：用户可能把操作理解成列表全选或单一出库动作，低估同时提交两类正式单据的影响。
- 运行证据：历史截图 E2。因含业务数据，本报告不附图。
- 源码位置：`wire_transfer_picker.js:123,895-925`、`wire_transfer_service.py:1197-1328`。
- 根因：界面文案只描述一个动作，没有描述完整单据链。
- 修复建议：改为“批量生成领料出库及整算单”。确认框列出将生成和提交的单据类型及数量。
- 修复后验证：空选择、混合库存/服务项目、已有关联单据、重复点击和失败回滚。
- 置信度：高。

### AUDIT-001：历史审计证据未脱敏且定位器不安全

- 严重级别：P1，属于审计交付风险，不属于业务应用缺陷。
- 页面与路由：22 个历史路由。
- 角色、公司、视口：历史管理员会话；三视口。
- 复现步骤：只读检查截图和 JSON 元数据。
- 预期结果：截图使用测试公司和脱敏数据。DOM 统计限制在当前 wrapper。日志记录 Console 与 Network 分类。
- 实际结果：部分截图包含员工、薪酬、账号和业务单据内容。准确版 JSON 的表格和行数跨页面累积。旧版 JSON 有 21 个 404。
- 用户与业务影响：审计材料本身泄露敏感信息，并产生错误的“全部通过”结论。
- 运行证据：88 张 PNG 与 2 个 JSON。文件指纹见附录。
- 源码位置：历史证据文件，不属于应用源码。
- 根因：测试未使用安全数据集，也未按当前 Page wrapper 限定定位器。
- 修复建议：废弃旧通过声明。重新使用脱敏测试站和 wrapper-scoped 定位器。
- 修复后验证：报告敏感扫描为 0。每个页面的表格数不跨页面累计。错误日志含请求 URL 和状态分类。
- 置信度：高。

## 八、P2 与 P3 详细发现

### SPA-001：11 个数据页面没有 `on_page_show`

- 严重级别：P2。
- 页面与路由：employee salary、jizhong、meal、monthly closing、monthly settlement、oil、payroll、qifu、reimbursement、tax、wire 共 11 页。
- 角色、公司、视口：所有获权角色；三个视口。
- 复现步骤：在测试站执行页面 A→B→A，并在 B 中改变相关业务状态。
- 预期结果：返回 A 后恢复实例，并按策略刷新数据、布局和工作上下文。
- 实际结果：本次未实测。静态统计 21 个 Page 中只有 10 个定义 `on_page_show`。
- 影响：返回后可能显示旧数据、旧高度或旧公司上下文。
- 证据：Page JS 静态统计。
- 根因：初始化和再次显示没有统一生命周期契约。
- 修复建议：共享标准 `on_page_show`。只刷新活动 wrapper 的必要区域。
- 修复后验证：每页 20 次 A→B→A，记录请求数和布局。
- 置信度：中高，代码风险。

### SPA-002：共享采购工作台全局事件没有解绑

- 严重级别：P2。
- 页面与路由：物料申请、采购执行、收货入库。
- 角色、公司、视口：采购和库存用户；1920×1080、1366×768。
- 复现步骤：反复切换三个页面，并改变工作上下文。
- 预期结果：只有活动 wrapper 收到事件。实例销毁时解绑。
- 实际结果：本次未实测。`bind_global_events()` 向 document 添加上下文和 wheel 事件，未见对应解绑。
- 影响：隐藏页可能重复刷新。事件和请求可能随页面访问增长。
- 证据：`public/js/procurement_workbench.js:137,234-237,346`。
- 根因：实例生命周期和全局监听生命周期不对称。
- 修复建议：使用命名空间处理器和 destroy。隐藏页不执行数据请求。
- 修复后验证：20 次路由往返后，每次事件只触发一次活动页请求。
- 置信度：中高。

### DRAFT-001：高频录入没有完整可恢复草稿证据

- 严重级别：P2。
- 页面与路由：报销、月结补录、自办电汇。
- 角色、公司、视口：相应操作员；三个视口。
- 复现步骤：录入多行后分别使用右上关闭、底部取消、页面切换、刷新和重开。
- 预期结果：输入、失焦、增删行和离开都保存草稿。重开后恢复。空表单不生成服务器垃圾草稿。
- 实际结果：关键 Dialog 已有静态背景，但文件中未发现覆盖关闭和重开的 `localStorage` 或 `beforeunload` 草稿引擎。
- 影响：长表录入可能丢失。
- 证据：`reimbursement_picker.js:735-824`、monthly settlement 和 wire Dialog 路径的文件级搜索。
- 根因：防误触和草稿恢复被当成同一问题，实际只完成前者。
- 修复建议：按页面、公司、期间和业务上下文建立草稿键。所有关闭出口使用同一 guard。
- 修复后验证：五种退出路径、跨公司隔离、提交后清除和存储不可用降级。
- 置信度：中高。

### UI-001：1,572 个存量内联样式

- 严重级别：P2。
- 页面与路由：跨模块。
- 角色、公司、视口：不适用。
- 复现步骤：运行 `scripts/verify_ui_style_governance.py`。
- 预期结果：新代码不增加内联样式。存量持续下降。
- 实际结果：本次输出 `1572`，基线上限 `1588`。门禁通过只说明没有增长。
- 影响：主题、响应式和组件维护成本高。
- 证据：本次只读脚本输出和 `ui_style_baseline.json`。
- 根因：治理目标只有“不增长”，没有模块递减计划。
- 修复建议：先抽取弹窗、表格、金额、状态、建议浮层和按钮 token。
- 修复后验证：每次改动降低总数，并做三视口视觉回归。
- 置信度：高。

### UI-002：原生 select 需要分类治理，不应一律胶囊化

- 严重级别：P2。
- 页面与路由：15 个 Page。
- 角色、公司、视口：三个视口。
- 复现步骤：检查 46 个字面量 `<select>` 的选项来源和数量。
- 预期结果：固定的 2至4项互斥状态使用分段控件。动态公司、仓库、年份和长列表使用可扩展选择器。
- 实际结果：源码有 46 个 select，分布在 15 页。旧报告要求把当前三家公司全部改为胶囊，这与动态公司原则冲突。
- 影响：固定小选项多一次点击。把动态集合强改胶囊又会导致溢出和维护问题。
- 证据：Page JS 静态统计。税票、电汇和库存历史截图显示实际选择器。
- 根因：缺少“固定互斥状态”和“动态业务集合”的组件决策表。
- 修复建议：逐控件分类。只改固定小集合。公司和仓库保持动态可搜索。
- 修复后验证：选项数 2、4、5、20 和窄屏场景。
- 置信度：高。

### UI-003：900px 首屏信息密度失衡

- 严重级别：P2。
- 页面与路由：祺富薪酬、税局发票、自办电汇。
- 角色、公司、视口：历史管理员会话；900px。
- 复现步骤：打开三个页面并观察第一屏可见的主业务行数。
- 预期结果：高频表格尽早进入视口。辅助说明可折叠或压缩。
- 实际结果：历史截图显示薪酬页先展示大标题、任务流程和计算中心。税票和电汇页先展示标题、多个 KPI、说明和筛选。主表可见行数有限。
- 影响：用户需要纵向滚动后才能开始主要工作。
- 证据：历史 E2 截图。因含敏感内容，本报告不附图。
- 根因：桌面布局按宽屏垂直节奏直接缩放到分屏。
- 修复建议：900px 下压缩说明、合并 KPI、固定筛选，并保持主表视口高度。
- 修复后验证：900px 首屏可见主表表头和至少 6 行测试数据。
- 置信度：中高。

### UI-004：薪酬金额缺少千分位

- 严重级别：P2。
- 页面与路由：薪酬综合核算，`/desk/payroll-settlement-workbench`。
- 角色、公司、视口：历史管理员会话；1920×1080。
- 复现步骤：查看薪资标准、加班工资和应发合计等金额列。
- 预期结果：金额统一显示货币符号、千分位和两位小数，并右对齐。
- 实际结果：历史截图中部分五位金额没有千分位。
- 影响：宽表快速核对和大额识别效率下降。
- 证据：历史 E2 截图。未复制敏感数据。
- 根因：部分单元格没有统一调用金额格式化函数。
- 修复建议：统一使用 AshanUI money formatter 和金额单元格 class。
- 修复后验证：零值、负数、五位、七位金额和导出对比。
- 置信度：中高。

### UI-005：自办电汇主按钮和操作列不统一

- 严重级别：P2。
- 页面与路由：自办电汇。
- 角色、公司、视口：历史管理员会话；1920×1080、900px。
- 复现步骤：查看新建按钮和每行关联单据动作。
- 预期结果：主操作使用全局主色。每行保留一个高频主动作，其余进入更多菜单。
- 实际结果：新建按钮使用专页紫色。行内可同时出现补建入库、补建出库、补建整算和新建付款等动作。
- 影响：视觉层级分裂。用户难以识别主动作。
- 证据：`wire_transfer_picker.css:428-449`、`wire_transfer_picker.js:861-883` 和历史 E2 截图。
- 根因：专页样式和单据链动作直接平铺。
- 修复建议：复用全局主按钮。保留一个上下文主动作，其余放入可访问的更多菜单。
- 修复后验证：键盘、焦点、窄屏和不同单据状态。
- 置信度：高。

### PAY-001：薪酬服务含固定公司和历史期间默认值

- 严重级别：P2。
- 页面与路由：员工薪酬、吉众薪酬、祺富薪酬。
- 角色、公司、视口：Payroll Operator；多公司、多期间；接口级。
- 复现步骤：在测试站省略 company 或 period 参数调用离职、社保和公积金批量方法。
- 预期结果：缺少公司或期间时拒绝，或从受权工作上下文动态解析。
- 实际结果：源码存在固定公司和历史月份默认值。
- 影响：遗漏参数时可能作用到错误公司或历史账期。
- 证据：`services/employee_salary_service.py:552-588,890,929` 和薪酬页面初始化常量。
- 根因：一次性企业/月份实现变成长期 API 默认值。
- 修复建议：关键上下文改为必填并校验。薪酬月和缴费月分别建模。
- 修复后验证：双公司、跨年一月、离职、零工资和公积金季度组合。
- 置信度：中高。

### COPY-001：装饰性图符和斜杠标题

- 严重级别：P3。
- 页面与路由：薪酬、税票、电汇、油卡、物业等。
- 角色、公司、视口：不适用。
- 复现步骤：扫描用户可见字符串，并人工区分装饰图符和功能性关闭符号。
- 预期结果：界面使用严谨中文。不同业务概念不以斜杠拼接。
- 实际结果：广义 Unicode 图符扫描在 35 个 JS/Python/HTML 文件中命中 1,012 行。该数字包含功能符号，不能等同于违规数量。人工复核确认多处装饰性图符。还确认了“发票/暂估号码”“出勤天/工时”“岗位/用工性质”“身份资料多概念拼接”等标题。
- 影响：视觉噪声高。字段语义和读屏表达不稳定。
- 证据：`wire_transfer_picker.js:97,603,621`、`qifu_hr_salary_workbench.js:717-739,1165-1168`、`lease_settlement_workbench.js:130`。
- 根因：历史页面各自维护文案和图符。
- 修复建议：建立用户可见文案清单。保留功能性关闭符号白名单。其他装饰符号改为纯文本或受控图标组件。
- 修复后验证：静态扫描和屏幕阅读器复核。
- 置信度：高。

## 九、旧报告结论裁决

| 旧结论 | 裁决 | 理由 |
|---|---|---|
| 22/22 路由全部实机通过 | 撤销 | 第一轮日志中 21 项为 404。第二轮只能证明历史渲染，定位器跨页面累积。 |
| 27 个核心页面全部 HTTP 200 | 无法确认 | 当前没有对应 27 项原始 Network 清单。第二份报告的证据目录不存在。 |
| 0 个 Console Error、0 个网络失败 | 撤销通过声明 | 历史 JSON 没有完整 Network 记录。第一轮明确记录 21 个 404。 |
| 所有写入 RPC 都使用 POST | 错误 | 当前源码保守确认至少 38 个默认 whitelist 写入入口。 |
| 25 个写入 RPC 未使用 POST | 方向正确，数量过时 | 当前保守下限为 38。 |
| 83 个 Dialog 中 68 个没有 static | 无法复现 | 当前源码只有 65 个 `new frappe.ui.Dialog` 构造。多个关键页面已有 static 或静态背景属性。 |
| 11 个 Page 缺少 on_page_show | 静态确认 | 21 个 Page 中 10 个有，11 个没有。仍需运行时证明实际影响。 |
| 14 个页面的 select 都应改胶囊 | 部分接受 | 当前是 15 页、46 个 select。只有固定 2至4项互斥状态应改。动态公司、仓库和年份不能机械改造。 |
| 库存台账四柱结构完整 | 代码层接受 | 服务端和前端都显示期初、流入、流出、期末和合计。运行数据未复算。 |
| 油卡四柱完全通过 | 撤销 | 结构存在，但草稿进入余额，不能判定财务通过。 |
| 个税 VBA 1:1 完全实机通过 | 未充分验证 | 函数和调用存在。当前没有安全、可重复的本次测试证据。现有根目录集成脚本会写真实业务数据，未运行。 |
| 原始凭证无损且不可篡改 | 撤销 | 税票清理服务物理删除原始 File。权限和保留规则也未收口。 |
| 自办电汇“全部出库”、紫色按钮、斜杠标题 | 接受 | 历史截图和当前源码互相支持。 |
| 900px 首屏被说明和 KPI 占用 | 接受为视觉缺陷 | 已抽查历史三页面截图。未作当前版本全量复测。 |

## 十、跨模块根因

1. 服务端授权经常绑定请求参数，不绑定最终 Document。正确顺序应是加载真实资源、读取真实公司、授权、校验状态、原子写入。

2. Page、DocPerm 和服务端授权模型没有同一事实源。新双角色模型和历史通用角色同时存在。

3. 自定义状态文本与 `docstatus` 混用。财务和库存结果因此可能包含草稿。

4. UI Kit 已存在，但专页仍复制 Dialog、按钮、筛选、金额和状态样式。

5. SPA 自动化没有限制当前 wrapper。历史缓存页污染标题、表格数和行数。

6. 测试站、测试公司和生产数据没有强制隔离。部分名为 test/verify 的脚本会写入或删除业务记录。

## 十一、整改路线图

### 11.1 立即处理

| 顺序 | 工作项 | 影响范围 | 回归风险 | 验收 |
|---:|---|---|---|---|
| 1 | 修复 OIL-001 的目标绑定和真实卡重算 | 油卡删除、余额、月结 | 高 | 双卡双公司负向测试和四柱复算 |
| 2 | 修复 OIL-002 的标准提交生命周期 | 油卡充值、加油、余额 | 高 | 草稿/提交/取消/回滚全链 |
| 3 | 收口 PROP-001 | 物业、租赁、封账 | 高 | 角色×公司×状态矩阵 |
| 4 | 收口 TAX-001 并停止普通接口物理删除原件 | 税局发票、File、归档 | 高 | 原件留存、权限和恢复演练 |
| 5 | 修复 INV-001 与 XSS-001 | 库存读取和材料出库 UI | 中高 | 双公司和隔离 XSS 测试 |
| 6 | 收口 COM-001、COM-002 | 合规和环保 | 中 | 角色与公司矩阵 |
| 7 | 将至少 38 个写入入口改为 POST | 跨模块 API | 中 | 方法、CSRF、权限和幂等测试 |
| 8 | 禁止危险测试脚本连接非测试站 | 验证工具 | 中 | 生产 URL 硬拒绝、无残留数据 |

### 11.2 低风险快速修正

- 修改自办电汇批量动作名称和确认文案。
- 统一电汇主按钮颜色和行操作层级。
- 修复薪酬金额千分位。
- 清理确认过的斜杠标题和装饰性图符。
- 删除薪酬服务中的历史期间默认值。

### 11.3 共享架构治理

- 建立统一的真实资源授权服务模板。
- 用同一配置生成 Page、DocPerm 和 RPC 角色测试。
- 为 11 个页面补充可验证的再次显示契约。
- 为共享工作台增加事件解绑、请求代次和隐藏页暂停。
- 为 Dialog 增加统一静态背景、双关闭和草稿接口。
- 把内联样式基线改成按模块逐步下降。
- 建立自动 UI surface registry，禁止混合口径重复计数。

### 11.4 需要业务负责人确认

- 油卡充值和加油是否默认直接提交。
- 税局发票原始 PDF 的法定留存年限和归档方式。
- 物业操作员、管理员的保存、核定和解锁动作矩阵。
- 固定公司薪酬工作台是否继续作为专属入口。
- 自办电汇批量动作是否应同时提交整算单。

### 11.5 暂不建议改动

- 不把动态公司、仓库和年份选择器一律改成胶囊。
- 不因性能问题删除既有视觉效果。先修事件、请求和局部渲染。
- 不在缺少测试站时运行会创建、提交、取消或删除单据的验证脚本。
- 不把历史截图中的“页面可见”解释为权限、财务和业务状态通过。

## 十二、后续实机验收矩阵

每个高风险页面必须在脱敏测试站完成以下场景：

1. 冷启动直达正确的连字符路由。
2. 页面 A→B→A 返回，定位器限制在当前可见 wrapper。
3. 正常、空、加载和可控错误状态。
4. 筛选、搜索、期间和公司切换。
5. 右上关闭、底部取消、Esc、Tab、Ctrl/Cmd+S 和草稿恢复。
6. 模块 Manager、Operator、通用角色和无权限角色。
7. 公司 A、公司 B 和伪造 company/warehouse 组合。
8. 1920×1080、1366×768 和约 900px。
9. Console、Network、请求取消、重复请求和响应大小。
10. 财务/库存业务的草稿、提交、取消、锁定、解锁和失败回滚。

验收结果必须区分预期 403、正常导航取消、环境 Socket.IO 基线和业务失败。

## 十三、证据附录

### 13.1 本次只读静态检查

| 检查 | 结果 |
|---|---|
| Desk Page JSON / JS | 21 / 21 |
| Workspace JSON | 7 |
| Script Report JSON | 15 |
| DocType JSON / 同名客户端 JS | 51 / 36 |
| `new frappe.ui.Dialog` 构造 | 65 |
| 字面量 `<select>` | 46，分布在 15 个 Page |
| 含 `on_page_show` 的 Page | 10 |
| 不含 `on_page_show` 的 Page | 11 |
| 明确名称的默认 whitelist 写入入口 | 至少 38 |
| UI 内联样式 | 1,572，基线上限 1,588，门禁通过 |
| 广义 Unicode 图符命中 | 1,012 行，35 个文件。含功能符号，不能直接等同违规数 |

### 13.2 历史证据指纹

以下文件包含敏感业务内容。本报告只记录指纹，不复制图片。

| 证据 | SHA-256 |
|---|---|
| `wire-transfer-picker_1080p.png` | `550A2833926F8859C80574018F4FF511433FE56B27AFE4CF346E171508618070` |
| `wire-transfer-picker_900px.png` | `B7F7CC750B441BF7D1224F79D8713B4A556267B9860F57F3AB54EB8AD6679B4F` |
| `payroll-settlement-workbench_1080p.png` | `D3E31BE405A134FF2733E69020CC1CBD80A7C414B03BD5CA3015FC651CCF6576` |
| `qifu-hr-salary-workbench_900px.png` | `573D581A001CC6FBE9EC04C0F350F12635BBF4CDCC227E0E6556A24594BB5941` |
| `tax-invoice-center_900px.png` | `E3A00CFB620261B7C570C128E74E92EBEC5E1454FB995C74F747D7167256F7B6` |
| `stock-ledger-workbench_900px.png` | `3FCF543DFD4FC724D4875C0BE189FDD3979C63A745DB449A27EE8605750BF04D` |
| `spa_audit_summary.json` | `57B935C0C9763CA67D02F5B4C9A8FD75683C881C82BA6C6BDF03E3E4715F973D` |
| `accurate_spa_summary.json` | `19AEDB09940E258385797F02A154ECCD5E705317CA63A979C9E209A60A664BF5` |

### 13.3 当前实机阻塞

本次在已连接的浏览器中重新访问授权 ERPNext 工作台。页面在加载阶段超时。没有可用的当前 DOM、Console 或 Network 结果。没有输入凭据，没有绕过认证，没有提交业务动作。

### 13.4 未运行的高风险检查

- `test_china_tax_integration.py` 会创建并提交 Purchase Invoice。本次未运行。
- 多个 scripts/scratch 工具含 insert、submit、delete 或 commit。本次没有运行这些工具。
- 油卡、物业、税票、特种设备和库存负向 RPC 场景需要隔离测试站。本次未执行。

### 13.5 官方语义依据

- Frappe Controller 生命周期：<https://docs.frappe.io/framework/user/en/basics/doctypes/controllers>
- Frappe 用户与权限：<https://docs.frappe.io/framework/user/en/basics/users-and-permissions>
- Frappe REST API：<https://docs.frappe.io/framework/user/en/api/rest>

官方资料只解释 Frappe 语义。项目结论以当前源码、metadata 和可用证据为先。

## 十四、完成状态

- 所有 21 个自定义 Desk Page 都有明确覆盖状态。
- 7 个 Workspace、15 个 Report、51 个 DocType、8 个 hooks 脚本入口和 7 个共享资源均已纳入清单。
- 每项产品缺陷都标明代码或历史证据等级。
- 旧报告中的实机通过结论已逐项接受、修正或撤销。
- 未验证项和阻塞项已列出。
- 新报告没有复制员工、薪酬、账号、发票、Token 或原始凭证内容。
- 本次没有修改应用源码、权限配置或业务数据。

本报告可以作为整改立项依据。P0/P1 关闭仍需脱敏测试站的角色、公司、状态和业务链验收。

# ERPNext 16 自定义工作台与 UI/UX 深度审计报告

审计日期：2026-08-28  
审计类型：只读代码与配置审计；运行时验收受阻  
审计对象：`ashan_cn_procurement` 自定义应用及其已注册 Desk UI 表面

## 审计结论摘要

本次自动发现并覆盖了 91 个自定义 UI 表面：21 个 Desk Page、15 个 Script Report、7 个 Workspace、33 个带客户端脚本的自定义 DocType、8 个 hooks 注册脚本入口，以及 7 个共享 UI 资源。所有 91 项均已完成代码和元数据审查；没有任何一项被标记为已实机验证。

授权 ERPNext 站点的登录页在首次只读访问时连接超时，且浏览器中没有可用的已登录会话。本次没有尝试凭据、绕过认证、提交测试单据或写入业务数据。因此，本文的 P0 至 P3 都是由可追溯源码路径证明的“代码风险”，不是已在生产或测试站点复现的运行时结论。浏览器截图、Console 和 Network 证据均为 0 项，不应被解释为“无异常”。

静态审计确认四项高优先级风险：油卡明细删除的对象绑定缺失、可提交油卡业务仅插入草稿即计入余额、物业月结写入与解锁接口未见鉴权收口、税局发票原始附件删除链路未见鉴权收口。它们分别可能破坏余额守恒、单据生命周期、公司范围或原始凭证不可篡改边界。

## 一、审查覆盖清单

### 1.1 方法、事实源与边界

已依次读取项目根目录 `AGENTS.md`、项目 ERPNext 定制与代码审查指引、`docs/ai/ERPNext_PROJECT_RULES.md`、应用 hooks、Page/Report/Workspace/DocType metadata、客户端资源、服务层和现有验证脚本。`scripts/verify_ui_style_governance.py` 已在只读条件下执行。

本地工作区不包含 Frappe 或 ERPNext v16 的 Controller 源码，也没有可用的本地容器运行时；因此 Controller 源码逐行审计被标记为阻塞。对 insert/submit 生命周期和权限语义，仅使用 Frappe 官方 Controller 与权限文档作交叉依据，未以模型记忆代替事实源。

运行时阻塞记录：`http://192.168.8.11:6888/login` 在浏览器导航后的 DOM 快照阶段超时；无已登录会话；没有暴露或尝试使用任何账号、Token、员工或工资信息。

状态说明：

| 状态 | 含义 |
|---|---|
| 仅代码审查 | 源码、JSON metadata、hooks 或已有测试已检查；没有运行时结论。 |
| 已实机验证 | 本次为 0 项。 |
| 阻塞 | 需要已授权站点或本地 v16 Controller 源码，当前不可取得。 |
| 无需适用 | 例如共享静态资源不单独具有 Desk 路由。 |

### 1.2 Desk Page（21 项，均为仅代码审查）

统一源码目录前缀：`ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/page/`。除明确标记为只读的展示区域外，以下页面均含业务写入、状态变更、导入、删除或其快捷入口，必须在后续测试站逐项验证。

| 模块 / Page | Desk 路由 | 主要源码 | 关联接口 / DocType | Page 允许角色 | 写入 | 状态 |
|---|---|---|---|---|---|---|
| 员工薪酬与人事档案台 | `/desk/employee-salary-workbench` | `employee_salary_workbench/*` | Employee Salary Profile；employee salary service | System Manager | 是 | 仅代码审查 |
| 环保管理 | `/desk/environmental-management` | `environmental_management/*` | Environmental Compliance Item；环境服务 | System Manager、Purchase Manager、Compliance Manager、Compliance Operator | 是 | 仅代码审查 |
| 吉众人事薪酬工作台 | `/desk/jizhong-hr-salary-workbench` | `jizhong_hr_salary_workbench/*` | 人事薪酬服务 | System Manager、HR Manager、HR User、Accounts Manager、Accounts User | 是 | 仅代码审查 |
| 房租物业月结 | `/desk/lease-settlement-workbench` | `lease_settlement_workbench/*` | Property Lease；物业结算服务 | System Manager、Administrator、Accounts Manager、Accounts User | 是 | 仅代码审查 |
| 收货入库 | `/desk/material-receipt-workbench` | `material_receipt_workbench/*` | Purchase Receipt；共享采购工作台 | System Manager、Stock Manager、Stock User | 是 | 仅代码审查 |
| 物料申请 | `/desk/material-request-workbench` | `material_request_workbench/*` | Material Request；共享采购工作台 | System Manager、Purchase Manager、Purchase User、Stock Manager、Stock User | 是 | 仅代码审查 |
| 工作餐费月结工作台 | `/desk/meal-settlement-workbench` | `meal_settlement_workbench/*` | 餐费月结服务 | System Manager、HR Manager、Accounts Manager、HR User | 是 | 仅代码审查 |
| 月度核定全景管理中枢 | `/desk/monthly-closing-center` | `monthly_closing_center/*` | 各模块封账接口 | System Manager、Payroll/Tax Invoice/Oil Card/Property/Compliance Manager 或 Operator、Accounts/HR Manager 或 User | 是 | 仅代码审查 |
| 月结补录 | `/desk/monthly-settlement-picker` | `monthly_settlement_picker/*` | 月结补录服务 | System Manager、Purchase/Stock/Accounts Manager 或 User | 是 | 仅代码审查 |
| 油卡综合台账明细台 | `/desk/oil-card-ledger` | `oil_card_ledger/*` | Oil Card、Recharge、Refuel Log；油卡台账服务 | Stock/Purchase/Accounts User、Oil Card Manager、Oil Card Operator、System Manager 及遗留油卡角色 | 是 | 仅代码审查 |
| 人事与薪酬月结工作台 | `/desk/payroll-settlement-workbench` | `payroll_settlement_workbench/*` | Payroll Settlement；薪酬服务 | System Manager、HR Manager、Accounts Manager | 是 | 仅代码审查 |
| 采购执行 | `/desk/procurement-execution-workbench` | `procurement_execution_workbench/*` | Purchase Order；共享采购工作台 | System Manager、Purchase Manager、Purchase User、Accounts Manager、Accounts User | 是 | 仅代码审查 |
| 水电费月结 | `/desk/property-settlement-workbench` | `property_settlement_workbench/*` | Property Monthly Settlement；物业结算服务 | System Manager、Accounts Manager、Accounts User、Property Manager、Property Operator | 是 | 仅代码审查 |
| 祺富人事薪酬工作台 | `/desk/qifu-hr-salary-workbench` | `qifu_hr_salary_workbench/*` | 人事薪酬服务 | System Manager、HR Manager、HR User、Accounts Manager、Accounts User | 是 | 仅代码审查 |
| 报销申请 | `/desk/reimbursement-picker` | `reimbursement_picker/*` | Reimbursement Request；报销服务 | System Manager、Purchase Manager、Purchase User、Accounts Manager、Accounts User | 是 | 仅代码审查 |
| 特种设备管理 | `/desk/special-equipment-center` | `special_equipment_center/*` | Special Equipment、Inspection；合规服务 | System Manager、Compliance Manager、Compliance Operator | 是 | 仅代码审查 |
| 材料出库 | `/desk/stock-issue-workbench` | `stock_issue_workbench/*` | Stock Entry、Bin；库存服务 | System Manager、Stock/Purchase/Accounts Manager 或 User | 是 | 仅代码审查 |
| 库存收发流水台账 | `/desk/stock-ledger-workbench` | `stock_ledger_workbench/*` | Stock Ledger Entry、Stock Entry；库存服务 | System Manager、Stock Manager、Stock User、Accounts Manager、Accounts User | 是 | 仅代码审查 |
| 税局发票 | `/desk/tax-invoice-center` | `tax_invoice_center/*` | Tax Invoice、File；发票清理服务 | System Manager、Accounts Manager、Accounts User | 是 | 仅代码审查 |
| 高速费月度台账大屏 | `/desk/vehicle-toll-ledger` | `vehicle_toll_ledger/*` | Vehicle Toll 系列 DocType；车辆服务 | Stock/Purchase/Accounts User、Oil Card Manager、Oil Card Operator、System Manager 及遗留油卡角色 | 是 | 仅代码审查 |
| 自办电汇 | `/desk/wire-transfer-picker` | `wire_transfer_picker/*` | Purchase Invoice、Payment Entry；电汇服务 | System Manager、Purchase/Stock/Accounts Manager 或 User | 是 | 仅代码审查 |

### 1.3 Script Report（15 项，均为仅代码审查）

统一目录：`ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/report/<report_name>/`。以下均为查询/图表表面，不因其本身带写入：Company Compliance Overview、Company Compliance Pending Purchase、Compliance Expiry Trend、Oil Card Balance Reconciliation、Oil Card Card Summary、Oil Card Monthly Ledger、Oil Card Operating Summary、Oil Card Recharge Ledger、Oil Supplier Invoice Summary、Property Settlement History、Reimbursement Payment Status、Unpaid Reimbursement List、Vehicle Fuel Cost Summary、Vehicle Monthly Fuel Trend、Vehicle Refuel Ledger。

### 1.4 Workspace（7 项，均为仅代码审查）

`Accounting and Finance`、`Company Compliance Center`、`My Business`、`Procurement Management`、`Property and Lease`、`Stock and Inventory`、`Vehicle Fuel Hub` 均发现为公开 Workspace metadata。它们本身不是数据权限的充分证据；但其可见入口应与 Page、DocPerm、RPC 三层权限一致，需在多角色实测中验证。

### 1.5 DocType 客户端增强（33 项，均为仅代码审查）

Ashan Employee Salary Profile、Ashan Holiday Calendar、Ashan Monthly Attendance、Ashan Payroll Settlement、Compliance Equipment Item、Employee Certificate Item、Environmental Compliance Item、Oil Card、Oil Card Invoice Batch、Oil Card Invoice Batch Item、Oil Card Monthly Closing、Oil Card Recharge、Oil Card Refuel Log、Property Charge Rate、Property Company Settlement Summary、Property Lease、Property Lease Charge、Property Meter Reading、Property Monthly Settlement、Property Settlement Adjustment、Reimbursement Invoice Item、Restricted Access Group、Restricted Access Group Role、Restricted Access Group User、Special Equipment、Special Equipment Annual Inspection、Special Equipment Inspection、Tax Invoice、Utility Meter、Vehicle Fuel Settings、Vehicle Toll Config、Vehicle Toll Deposit、Vehicle Toll Monthly Sheet。

`hooks.py` 另注册 3 个表单脚本（Purchase Invoice、Reimbursement Request、Vehicle）和 5 个列表脚本（Material Request、Purchase Order、Purchase Receipt、Purchase Invoice、Reimbursement Request），均已纳入静态审查。

### 1.6 共享资源、弹窗与快捷操作（均为仅代码审查）

共享资源：`public/css/ashan_ui_kit.css`、`public/js/ashan_ui_kit.js`、`public/css/ashan_cn_procurement.css`、`public/js/ashan_work_context.js`、`public/js/ashan_cn_sidebar_v2.js`、`public/js/doc_details_list.js`、`public/js/procurement_workbench.js`。

已把父页面内的快捷操作和弹窗纳入覆盖：报销创建/编辑/详情、月结补录、收货入库、物料申请、采购执行、电汇建单/收货/付款、材料出库/库存选择、库存台账快捷出库、油卡建卡/充值/加油/锁定/删除、税局发票上传/匹配/清理、物业月结结算/解锁、特种设备快速建档和检验。共享组件不能替代运行时单独验收。

## 二、总体健康度评分卡

| 维度 | 评级 | 证据与限制 |
|---|---|---|
| 业务与财务严谨性 | D | 发现 4 项 P0 代码风险，涉及油卡余额、可提交单据生命周期、物业月结和原始发票附件。台账四柱守恒的视觉和数值结果未实机验证。 |
| 权限与代码架构 | D | Page、DocPerm 和服务层角色模型存在显著漂移；37 个状态性 RPC 未显式限制为 POST；多处 `ignore_permissions` 未见同层鉴权。 |
| UI 设计系统一致性 | C | 样式治理脚本通过，但仍有 1,572 个 HTML 内联样式，且 20 个文件发现装饰性图符文本。 |
| 人机工程与操作效率 | C | 报销、月结补录、电汇等高频录入未发现端到端草稿恢复；部分页面已经采用静态背景和双关闭出口。未经实机验证。 |
| 稳定性与性能 | C | 共享采购工作台在 document 上累积事件监听的代码风险可能导致缓存页重复请求；网络、性能和内存未能运行验证。 |
| 响应式与可访问性 | 未充分验证 | 1920×1080、1366×768、约 900px 的浏览器验收均因站点阻塞而未执行。 |

## 三、各模块深度审查与发现

### 3.1 发现清单

所有发现的角色、公司和视口字段均如实记录。标记为“未执行”的复现步骤是建议后续在隔离测试站执行的场景，并非本次已写入或已利用的操作。

#### OIL-001 — P0 — 删除对象未绑定油卡与期间

- 模块/路由：油卡与车辆；`/desk/oil-card-ledger`。
- 角色、公司、视口：需要 Oil Card Manager 或具备 `unlock_approve` 的测试角色；测试公司 A/B；未执行，视口不适用。
- 复现步骤：在隔离测试站创建两张归属不同公司或范围的测试油卡及各自流水；以仅获卡 A 授权的角色调用删除 API，参数传卡 A 和卡 B 的流水名称；再读取卡 B 余额。
- 预期：服务端重新加载目标流水，确认其油卡、公司和业务期间均等于受权上下文后才允许删除，并重算目标卡。
- 实际：本次未执行。静态路径显示 `delete_ledger_record()` 仅对传入 `oil_card` 调用 `assert_oil_ledger_access()`，随后按传入 `doc_type`/`name` 直接 `frappe.delete_doc(..., ignore_permissions=True)`；未见目标 Document 的油卡、公司和年月绑定校验。
- 影响：可删除不属于受权油卡的记录；被删油卡可能不被重算，破坏账实一致和四柱守恒追溯。
- 证据：`page/oil_card_ledger/oil_card_ledger.py:823-873`。
- 根因：授权对象与被删除对象分离，且以受控参数而非已加载 Document 建立授权边界。
- 修复建议：先加载目标 Document；从其油卡、公司、凭证日期导出安全上下文；逐项匹配请求参数或忽略请求参数；通过后执行删除并在同一事务重算真实油卡。记录删除原因、操作者和前后余额。限制为 POST。
- 修复后验证：两个公司、两张卡、管理员/操作员/无权角色的正负向测试；核对删除前后流水、期初、本期流入/流出、期末余额闭环。
- 结论置信度：高，代码风险，未实机验证。

#### OIL-002 — P0 — 可提交油卡业务在草稿状态即计入余额

- 模块/路由：油卡与车辆；`/desk/oil-card-ledger`。
- 角色、公司、视口：Oil Card Operator；隔离测试公司；未执行，视口不适用。
- 复现步骤：在测试站通过快捷充值或快捷加油创建一条记录；检查其 `docstatus`、页面显示状态和油卡余额；随后取消草稿或直接检查台账查询条件。
- 预期：标记 `is_submittable: 1` 的业务记录必须通过 `submit()` 进入正式状态后才改变余额；草稿不应进入正式台账。
- 实际：本次未执行。`Oil Card Recharge` 与 `Oil Card Refuel Log` metadata 为可提交 DocType；`quick_add_refuel()` 和 `quick_add_recharge()` 均调用 `doc.insert(ignore_permissions=True)` 后重算余额，未见 `doc.submit()`。设置文本字段 `status = "Submitted"` 不会改变 Frappe 的 `docstatus`。
- 影响：界面状态、Frappe 生命周期与余额可能不一致；草稿、撤销和审计链无法可靠表达真实业务。
- 证据：`doctype/oil_card_recharge/oil_card_recharge.json` 与 `doctype/oil_card_refuel_log/oil_card_refuel_log.json` 的 `is_submittable`；`page/oil_card_ledger/oil_card_ledger.py:568-622,655-694`。
- 根因：以自定义状态文本代替标准提交生命周期，余额查询未严格只纳入已提交凭证。
- 修复建议：明确业务模式：若即时过账，使用标准 `insert` 后 `submit` 并以 `docstatus=1` 记账；若需草稿，则余额查询仅纳入已提交记录。写入与重算必须同一事务，并限制为 POST。
- 修复后验证：草稿、新建提交、取消、重复提交、失败回滚的余额和台账四柱守恒测试。
- 结论置信度：高，代码风险，未实机验证。

#### PROP-001 — P0 — 物业月结写入、封账与解锁接口未见服务端收口

- 模块/路由：物业与租赁；`/desk/property-settlement-workbench`、`/desk/lease-settlement-workbench`。
- 角色、公司、视口：任意已认证 Desk 用户为风险假设；多公司测试环境；未执行，视口不适用。
- 复现步骤：在隔离测试站以无 Property 角色的普通用户直接调用保存、核定、解锁、租约发票更新和账单读取 RPC；观察访问控制、公司范围和审计字段。
- 预期：每个入口应为 POST；以重新加载的 Document、公司和状态为准，调用模块权限及公司权限校验；解锁需管理员级角色、原因和审计记录。
- 实际：本次未执行。Page wrapper 多个 `@frappe.whitelist()` 入口直接委托服务；物业服务写入租约发票、保存月结、核定和退回草稿均使用 `ignore_permissions`，未发现同层 `assert_company_access()`、`assert_module_access()` 或 `frappe.has_permission()`。
- 影响：跨公司读取、无权写入、无理由解锁封账以及租约发票对账被改变的风险；月结严肃性和审计边界失效。
- 证据：`page/property_settlement_workbench/property_settlement_workbench.py:17-45,119`；`services/property_settlement.py:161-195,901-995`。
- 根因：Page RPC 视为可信 UI 调用，服务层没有以不可信请求重新建立权限和状态边界。
- 修复建议：所有变更入口改为 `methods=["POST"]`；服务层集中检查 `Property Manager/Operator` 动作矩阵、每个涉及公司的 `assert_company_access()`、Document 权限和 `docstatus/status`；封账/解锁保存不可修改审计事件及理由。
- 修复后验证：管理员、操作员、Accounts 用户、无权用户在两个公司下的读写/封账/解锁矩阵；接口直接调用与页面调用结果一致。
- 结论置信度：高，代码风险，未实机验证。

#### TAX-001 — P0 — 税局发票原始附件清理链路缺少可见授权边界

- 模块/路由：税局发票；`/desk/tax-invoice-center`。
- 角色、公司、视口：任意已认证 Desk 用户为风险假设；测试发票及附件；未执行，视口不适用。
- 复现步骤：在隔离测试站，以 Tax Invoice Operator、普通 Accounts 用户和无关用户分别直接调用上传、放弃、恢复、重匹配、删除 PDF、配置保存与清理 RPC；检查附件、Tax Invoice 和 File 审计轨迹。
- 预期：原始凭证的删除或替换应有 POST、模块权限、公司权限、Document 状态校验和不可篡改审计；普通操作不应直接物理删除原始凭证。
- 实际：本次未执行。上传、状态变更、删除 PDF、设置保存和清理等多个入口为默认 `@frappe.whitelist()`；`delete_tax_invoice_pdf()` 直达清理服务。清理服务加载 Tax Invoice 后删除关联 File 并以 `ignore_permissions` 保存，未见调用方级别的模块或公司校验。
- 影响：原始凭证可被未授权调用路径删除或业务状态被变更，造成审计证据缺失和不可恢复风险。
- 证据：`page/tax_invoice_center/tax_invoice_center.py:262-295,358-465`；`services/tax_invoice_cleanup.py:5-35`。
- 根因：敏感文件操作与业务状态操作依赖前端可见性，未在最终服务动作建立授权与保全规则。
- 修复建议：将凭证上传、匹配、状态变更、配置更新和清理逐个映射到授权动作；全部 POST；删除改为受控归档/作废记录，保留二进制原件或合规留存副本；记录操作者、理由、原 File 标识和哈希。
- 修复后验证：多角色、多公司、已封账/已归档凭证、重复附件和失败事务测试；确认任何非法调用均被拒绝且不修改 File。
- 结论置信度：高，代码风险，未实机验证。

#### AUTH-001 — P1 — Page、DocPerm 与模块双角色模型存在配置漂移

- 模块/路由：油卡、物业、税局发票、薪酬等多个模块；相应 Desk 路由见 1.2。
- 角色、公司、视口：metadata 审查；视口不适用。
- 复现步骤：在测试站导出每个受影响 DocType 的 DocPerm，逐个以模块管理员、模块操作员、Accounts User、Purchase User、Stock User、HR User 登录并尝试进入 Page、打开表单和直调 RPC。
- 预期：自定义模块只保留项目规定的管理员/操作员角色对；Page、DocPerm、服务端动作三层一致；平台管理员是例外，不形成第三业务角色。
- 实际：本次未执行。`authorization_service.py` 已定义 Payroll、Oil Card、Compliance、Property、Tax Invoice 的 Manager/Operator 对；但多个 Page JSON 和 DocType JSON 仍授予泛用 Accounts、Purchase、Stock 或 HR 角色入口和写入/提交权限。物业租约 metadata 中泛用 Accounts 角色的权限强于模块角色的情形尤其值得复核。
- 影响：最小权限被稀释，前端入口、表单权限和 RPC 行为可能出现不一致或越权。
- 证据：`services/authorization_service.py` 的 `MODULE_ACCESS_MODEL`；`page/oil_card_ledger/oil_card_ledger.json:15-21`、`page/property_settlement_workbench/property_settlement_workbench.json:16-17`、`page/tax_invoice_center/tax_invoice_center.json:18-21`、薪酬 Page metadata，以及相关 Oil Card、Property Lease、Tax Invoice、Ashan Monthly Payroll Settlement 的 JSON DocPerm。
- 根因：新授权服务与历史 Page/DocType metadata 并行演进，未设置配置一致性测试或迁移清单。
- 修复建议：由业务负责人确认每模块动作矩阵后，统一收敛 Page.roles、DocPerm 和 RPC；添加 metadata 审计测试，阻止泛用角色重新获得模块权限。
- 修复后验证：完整角色×页面×DocType×RPC 矩阵；负向 403 与正向正常流程分开记录。
- 结论置信度：高，代码配置风险，未实机验证。

#### RPC-001 — P1 — 37 个状态性 RPC 未显式限制 HTTP POST

- 模块/路由：油卡、物业、税局发票、特种设备、车辆高速费、餐费、节假日和定期处理等；涉及页面见 1.2。
- 角色、公司、视口：代码审查；视口不适用。
- 复现步骤：在隔离测试站对每个写入 API 以 GET/POST 分别调用，观察 Frappe 路由方法拒绝、CSRF 和业务数据变化。
- 预期：所有写入、导入、删除、审批、状态变更与封账接口必须使用 `@frappe.whitelist(methods=["POST"])`。
- 实际：本次未执行。AST 静态扫描发现 37 个含写入或状态改变的默认 `@frappe.whitelist()` 函数；例如油卡快速建档、充值、加油、锁定、解锁、删除位于 `page/oil_card_ledger/oil_card_ledger.py:167-873`，税局发票与物业入口见 TAX-001、PROP-001。
- 影响：违反项目 API 纪律，扩大请求方法与 CSRF/误调用面；其可利用性需要在测试站按版本配置验证。
- 证据：项目规则的 POST 要求；上述文件以及 `page/special_equipment_center/`、`page/vehicle_toll_ledger/`、餐费与人事周期服务中的静态扫描结果。
- 根因：将默认 whitelist 用于读写混合接口，未建立 API 方法门禁。
- 修复建议：逐个分类读写 RPC；所有改变状态的 API 显式 POST，读取 API 只返回经权限过滤的数据；加入 AST/CI 规则阻断新的违规入口。
- 修复后验证：API 方法矩阵、CSRF 负向测试、重复请求幂等测试。
- 结论置信度：高，代码风险，未实机验证。

#### INV-001 — P1 — 库存可用量查询未从仓库反向校验公司

- 模块/路由：材料出库；`/desk/stock-issue-workbench`。
- 角色、公司、视口：具有公司 A 库存访问权的测试角色；公司 A/B、仓库 B；未执行，视口不适用。
- 复现步骤：在测试站以仅公司 A 授权用户，传入 `company=A` 与属于公司 B 的 warehouse；比较返回物料与直接访问公司 B 的结果。
- 预期：仓库必须经服务端解析并验证属于所选且受权的公司；查询不能仅信任调用方传入公司。
- 实际：本次未执行。`get_warehouse_stock_items()` 仅对传入 `company` 调用 `assert_company_access(company)`，查询 `tabBin` 时按 `b.warehouse` 过滤，未见与 `tabWarehouse.company` 的连接或仓库归属验证。
- 影响：若用户知道或可猜测其他公司的仓库标识，可能读到跨公司库存可用量。
- 证据：`page/stock_issue_workbench/stock_issue_workbench.py:441-480`。
- 根因：安全检查绑定在请求参数而非被查询资源。
- 修复建议：加载 Warehouse，核验 company 与 `assert_company_access(warehouse.company)`；SQL 加入仓库公司约束，并只返回受权仓库。
- 修复后验证：公司 A/B、有效/伪造组合、无仓库权限及管理员场景；记录预期 403 与空结果的区别。
- 结论置信度：高，代码风险，未实机验证。

#### XSS-001 — P1 — 材料出库页面将业务字段直接拼入 HTML

- 模块/路由：材料出库；`/desk/stock-issue-workbench`。
- 角色、公司、视口：可提交备注或可控制物料描述的测试角色；隔离测试公司；未执行，建议 1366×768 验收。
- 复现步骤：仅在隔离测试记录中写入带 HTML 特殊字符的备注、物料名称和用途；再以另一测试用户打开工作台与详情弹窗，检查 DOM 是否被转义，Console 是否出现脚本执行或异常。
- 预期：所有不可信业务字段在插入 HTML 前统一转义；属性值使用安全 DOM API 或属性编码。
- 实际：本次未执行，未写入任何测试载荷。源码以模板字符串将 `purpose_label`、`remarks`、`item_name`、`description` 等字段直接插入元素文本和 `data-*` 属性，文件内未发现统一 `escapeHtml` 处理。
- 影响：受控业务字段可能形成存储型 XSS，影响打开该页面的其他用户。
- 证据：`page/stock_issue_workbench/stock_issue_workbench.js:447-451,560-569,1027,1097-1106,1435-1436`。
- 根因：使用字符串拼接渲染不可信业务数据。
- 修复建议：改用 DOM 节点的 `.text()`/`textContent`，或统一可靠的 HTML/属性转义函数；对已有记录作数据清理评估。
- 修复后验证：隔离环境 OWASP 字符集回归、详情/建议浮层/购物车/打印预览全路径检查，以及 Console 0 error。
- 结论置信度：高，代码风险，未实机验证。

#### COM-001 — P1 — 特种设备快捷写入接口未见模块和公司权限校验

- 模块/路由：特种设备与合规；`/desk/special-equipment-center`。
- 角色、公司、视口：普通 Desk 用户与 Compliance Operator/Manager；隔离测试公司；未执行，视口不适用。
- 复现步骤：在测试站用三类角色直调快速建档、检验和年检接口，核对拒绝行为与公司绑定。
- 预期：新建设备、检验和年检必须 POST，并在服务端检查 Compliance 动作权限、公司权限及关联设备状态。
- 实际：本次未执行。`quick_create`、`quick_add_inspection`、`quick_add_annual_inspection` 是默认 whitelist，使用 `ignore_permissions` 插入并提交；未在该文件中发现模块/公司权限断言。
- 影响：合规台账可能被非授权角色创建或更改，证照与检验完整性不可保证。
- 证据：`page/special_equipment_center/special_equipment_center.py:142-247`。
- 根因：快捷入口直接承担业务写入，没有复用授权服务。
- 修复建议：收口至合规服务的受权 POST 方法，重载关联 Document 并核验公司、角色和状态；补全审核日志。
- 修复后验证：三角色、两公司、重复检验和过期设备情形的正负向测试。
- 结论置信度：高，代码风险，未实机验证。

#### COM-002 — P1 — 环保看板默认查询未建立公司范围

- 模块/路由：环保管理；`/desk/environmental-management`。
- 角色、公司、视口：具有一个公司访问权的测试用户；公司 A/B；未执行，视口不适用。
- 复现步骤：在测试站不传 company、传公司 A、传公司 B 分别请求看板读取接口，比较返回集合；再以无 Compliance 角色的泛用 Purchase Manager 测试。
- 预期：读取应从用户受权公司集合开始过滤，不能先取全量再由请求参数筛选。
- 实际：本次未执行。看板读取在 company 存在时才调用公司权限检查；默认分支从全量环境合规项读取，并返回全公司列表。写入入口已观察到 POST 与公司权限调用，这一正向实现不能弥补读取默认范围问题。
- 影响：跨公司合规台账和期限信息可能暴露给仅有局部权限的用户。
- 证据：`page/environmental_management/environmental_management.py:16-33,127` 的 `get_environmental_dashboard_data()`；其写入方法与读取方法的权限分支。
- 根因：读取 API 把 company 当可选筛选条件，而不是强制安全边界。
- 修复建议：从 `get_allowed_companies()` 生成服务器端范围；无受权公司时拒绝；Page.roles 与 Compliance Manager/Operator 模型对齐。
- 修复后验证：两公司与四角色下的默认/显式 company 请求矩阵。
- 结论置信度：中高，代码风险，未实机验证。

#### DRAFT-001 — P2 — 多个高频弹窗缺少可恢复草稿保护

- 模块/路由：报销申请、月结补录、自办电汇；`/desk/reimbursement-picker`、`/desk/monthly-settlement-picker`、`/desk/wire-transfer-picker`。
- 角色、公司、视口：相应操作员；测试公司；未执行，建议三个规定视口均验证。
- 复现步骤：在隔离测试站打开新建弹窗、输入多行数据后分别点击右上角关闭、底部取消、切换 Desk 页面、刷新浏览器和重新打开弹窗；检查是否恢复且空表单不会生成服务器草稿。
- 预期：输入防抖、失焦、Tab、增删行、页面离开及两条关闭路径使用同一草稿保护逻辑；重新打开完整恢复。
- 实际：本次未执行。以上三个页面的源码未发现 `localStorage` 或 `beforeunload` 草稿恢复实现。报销弹窗已使用静态背景并有关闭入口，属于部分达标，不能替代持久草稿保护。
- 影响：高频录入在误关、页面跳转或网络中断时有丢失风险，且不同关闭入口可能呈现不一致行为。
- 证据：`page/reimbursement_picker/reimbursement_picker.js:735-824`；`page/monthly_settlement_picker/monthly_settlement_picker.js`；`page/wire_transfer_picker/wire_transfer_picker.js` 的 Dialog 创建与关闭路径；文件级静态搜索结果。
- 根因：弹窗视图生命周期未接入共享草稿引擎。
- 修复建议：提供页面命名空间+公司+期间+业务上下文的本地草稿键；统一 close guard；成功提交后清除；不得在空表单时创建服务器草稿。
- 修复后验证：每个关闭路径、断网重开、跨公司/跨期间隔离、提交成功清理、浏览器存储不可用降级。
- 结论置信度：中高，代码风险，未实机验证。

#### SPA-001 — P2 — 共享采购工作台在全局 document 累积事件监听

- 模块/路由：物料申请、采购执行、收货入库；`/desk/material-request-workbench`、`/desk/procurement-execution-workbench`、`/desk/material-receipt-workbench`。
- 角色、公司、视口：任意获权采购/库存用户；未执行，建议 1920×1080 和 1366×768。
- 复现步骤：在测试站按 A→B→C→A 多次切换三页面并改变工作上下文；统计请求数、事件回调数、Console 和内存中实例数。
- 预期：每个 wrapper 只有一个活动实例；隐藏缓存页不接收不必要更新；页面卸载时解除 document 监听。
- 实际：本次未执行。`mount()` 对 wrapper 缓存实例是正向设计；但 `bind_global_events()` 使用 `document.addEventListener("ashan-work-context-changed", ...)` 和 `$(document).on("wheel", ...)`，未见对应解绑或 destroy。
- 影响：Frappe SPA 缓存多个页面后可能重复请求、重复滚轮处理、性能下降或隐藏页状态被更新。
- 证据：`public/js/procurement_workbench.js:137,234-237,346`。
- 根因：共享实例生命周期与全局事件生命周期不对称。
- 修复建议：保存命名空间事件处理器，提供 `destroy()`/`on_page_hide()` 解绑；或仅为活动 wrapper 订阅上下文事件，并以 AbortController/请求代次取消旧请求。
- 修复后验证：连续 20 次路由往返，Network 请求数不增长、每次上下文改变只触发一个活动页面、Console 0 error。
- 结论置信度：中高，代码风险，未实机验证。

#### UI-001 — P2 — 样式治理未阻止存量内联样式债务

- 模块/路由：跨模块；尤其人事薪酬、物业、油卡、税局发票、餐费等页面。
- 角色、公司、视口：不适用；静态检查。
- 复现步骤：运行 `scripts/verify_ui_style_governance.py`，并按页面统计 `style=` 属性。
- 预期：项目规则要求新代码不增加内联样式，设计令牌和共享组件以 UI Kit 作为唯一入口；存量应有明确的递减治理计划。
- 实际：脚本成功，输出 `Inline styles: 1572 (baseline ceiling: 1588)` 与“未新增”。这证明门禁防止增长，但不证明设计系统已收敛。人事薪酬、物业等页面仍有大量 legacy 内联样式。
- 影响：响应式调整、主题一致性、无障碍修复和组件复用成本显著升高；静态门禁可能掩盖存量风险。
- 证据：`ui_style_baseline.json`；`scripts/verify_ui_style_governance.py` 的本次输出；例如 `page/qifu_hr_salary_workbench/qifu_hr_salary_workbench.js:1197` 及相关页面。
- 根因：基线只约束“不得增加”，缺少按模块递减、抽取共享 token 的迁移目标。
- 修复建议：不放宽门禁；按高频页面设立递减基线，先抽取表格、弹窗、金额单元格和状态表达的重复样式至 `ashan_ui_kit.css`。
- 修复后验证：每次变更使内联样式总量下降；三视口视觉回归、focus-visible 和高对比检查通过。
- 结论置信度：高，已执行静态检查；视觉影响未实机验证。

#### PAY-001 — P2 — 薪酬服务存在固定公司/历史期间默认值

- 模块/路由：员工薪酬、吉众人事薪酬、祺富人事薪酬；相应 Desk 路由见 1.2。
- 角色、公司、视口：薪酬操作员；测试公司与不同账期；未执行，视口不适用。
- 复现步骤：在测试站不传 company 或 period 参数直接调用相关查询/离职/社保公积金批量接口；检查实际落点和界面默认账期。
- 预期：公司、账期和人员集合由受权上下文或显式参数动态获取；缺失关键参数时拒绝，不应静默使用历史固定值。
- 实际：本次未执行。薪酬服务与多个前端页面发现固定公司和历史月份默认值；其中批量离职与缴费相关方法在未传参时可落到固定默认上下文。固定公司工作台是否是被批准的专属入口需业务负责人确认，但历史账期默认值不符合动态处理原则。
- 影响：直调 API、重新打开旧页面或遗漏参数时可能查询或写入错误公司/期间，损害薪酬月与缴费月双时钟严谨性。
- 证据：`services/employee_salary_service.py:552-588,890,929` 的默认参数；`page/qifu_hr_salary_workbench/`、`page/jizhong_hr_salary_workbench/`、`page/employee_salary_workbench/` 的初始化常量。
- 根因：从一次性企业/月份实现遗留的默认上下文未彻底动态化。
- 修复建议：公司和期间必须显式传入并经授权校验，或由当前工作上下文动态解析；薪酬核算月与缴费凭证月分别建模，缺参直接报错。
- 修复后验证：两公司、跨年一月、离职人员、零工资、社保和公积金季度月份组合测试；与人工核对表比对。
- 结论置信度：中高，代码风险，未实机验证。

#### COPY-001 — P3 — 多个系统界面含未经授权的装饰性图符文本

- 模块/路由：跨模块；含薪酬、出库、油卡等 Page。
- 角色、公司、视口：不适用；静态检查。
- 复现步骤：扫描 Page JS、DocType JS、服务提示文本的 Unicode 图符，并在后续测试站检查用户可见文案。
- 预期：除用户明确要求外，界面文本、按钮、提示和注释不使用装饰性 Emoji；功能性关闭符号可按设计规范单独评估。
- 实际：静态扫描在 20 个文件中命中 384 行包含装饰性图符的文本；例如部分薪酬页标题与库存操作提示。未将功能性关闭符号计为本项。
- 影响：与项目严肃企业界面规范不一致，且可能降低屏幕阅读器语义和文本检索一致性。
- 证据：`page/qifu_hr_salary_workbench/qifu_hr_salary_workbench.js:4`、`page/employee_salary_workbench/employee_salary_workbench.js:4`、`page/jizhong_hr_salary_workbench/jizhong_hr_salary_workbench.js:4` 及扫描索引。
- 根因：历史界面文案未经过统一设计治理。
- 修复建议：将状态以颜色、图标组件的可访问名称和准确中文文案表达；统一清理装饰性文本图符。
- 修复后验证：静态扫描归零（保留经批准的功能性符号白名单），屏幕阅读器与中文文案回归。
- 结论置信度：高，代码证据；实际可见性未实机验证。

### 3.2 已观察到的正向实现（不等于运行时通过）

- 报销服务的创建与删除路径已见 `methods=["POST"]`、公司断言及仅允许删除草稿的前置校验：`services/reimbursement_picker_service.py:891,981-988`。仍需在角色和单据链实测。
- 月结补录与电汇服务的主要创建入口已见 POST 与公司权限调用：`services/monthly_settlement_service.py:391-400`、`services/wire_transfer_service.py:664-687`。仍需验证失败回滚、重复提交和 UI 局部刷新。
- 库存台账快捷出库和材料出库创建入口已见 POST 与公司断言：`page/stock_ledger_workbench/stock_ledger_workbench.py:762`、`page/stock_issue_workbench/stock_issue_workbench.py:534-551`。这不抵消 INV-001 与 XSS-001。
- 报销新建弹窗源码已见静态背景和可见关闭入口；这只是弹窗防误触的代码层部分达标，草稿保护仍未得到证明。
- 环保写入路径已见 POST 与公司权限调用；默认读取范围问题仍需整改。

### 3.3 各模块未验证项与阻塞原因

所有 10 个最低模块及其自动发现的 Page/Report/Workspace/DocType 均受相同运行时阻塞影响。未完成的现场验证包括：冷启动、A→B→A 返回、正常/空/错误状态、筛选/期间切换、弹窗草稿恢复、管理员/操作员/无权角色、不同公司、三种视口、Console、Network、冻结列同步、键盘导航和重复请求。阻塞原因仅为站点连接超时和无授权会话；不是功能通过的证据。

### 3.4 最低业务模块审查矩阵

| 模块 | 已观察到的达标项（代码层） | 缺陷 / 风险编号 | 未验证内容与阻塞 |
|---|---|---|---|
| 采购协同与岗位工作台 | 共享工作台按 wrapper 缓存实例。 | SPA-001、AUTH-001、RPC-001、UI-001 | 物料申请、采购执行、收货入库的往返路由、重复请求、角色入口、宽表与三视口均被站点连接阻塞。 |
| 物料申请、采购执行、收货入库和采购总览 | 三个工作台已注册并复用共享资源。 | SPA-001、AUTH-001、RPC-001 | 未取得正常、空、异常数据态或任何 Network 记录。 |
| 报销申请中心 | 创建/删除服务已见 POST、公司断言和“仅草稿删除”检查。 | DRAFT-001、AUTH-001 | 新建、编辑、详情、附件、付款链和草稿恢复均未实测。 |
| 月结入库工作台 | 主创建服务已见 POST 和公司断言。 | DRAFT-001、RPC-001、UI-001 | 入库单生成、重复点击、失败回滚、表头/滚动同步均未实测。 |
| 自办电汇工作台 | 主创建服务已见 POST 和公司断言。 | DRAFT-001、RPC-001、AUTH-001 | 发票、收货、付款、关闭弹窗、草稿和审批边界均未实测。 |
| 薪酬综合核算中心 | Page 和相关 DocType 表面均已纳入发现清单。 | AUTH-001、PAY-001、UI-001、COPY-001 | 人员集合、零工资、税务累计、薪酬月/缴费月、不同公司和敏感数据脱敏验证均未执行。 |
| 油卡与车辆管理工作台 | 常规动作已使用 `assert_oil_ledger_access()`；该机制不能覆盖 OIL-001 的绑定缺口。 | OIL-001、OIL-002、AUTH-001、RPC-001、COPY-001 | 双卡/双公司、提交/取消、余额守恒、锁定/解锁和车辆高速费全部未实测。 |
| 特种设备与合规台账 | 环保写入路径已见 POST 和公司权限调用。 | COM-001、COM-002、AUTH-001、RPC-001 | 设备建档、检验、到期预警、无权角色和跨公司读取均未实测。 |
| 物业与租赁管理工作台 | 静态页面与服务完整纳入审查。 | PROP-001、AUTH-001、RPC-001、UI-001 | 计量读数、期间结转、公司间调整、封账/解锁、账单打印和多视口弹窗均未实测。 |
| 税局发票协同台账 | 已识别上传、匹配、恢复、清理等完整操作面。 | TAX-001、AUTH-001、RPC-001、UI-001 | 文件原件、上传 ZIP、状态链、封账关联、不同角色和不可逆删除均未实测。 |
| 自动发现的其他 Page、Report、Workspace、DocType 增强 | 见覆盖清单，均未漏出审查范围。 | UI-001、COPY-001，及按所在服务继承的 AUTH-001/RPC-001 | 所有运行时路径均同样受站点连接与会话阻塞。 |

## 四、跨模块共性问题

1. 权限边界没有在最终资源上重建。多处先校验调用方传入的 company 或业务对象，再按其他名称加载/删除真正资源。应采用“加载真实 Document → 导出 company/关联对象 → 授权 → 状态校验 → 原子写入”的统一服务模板。

2. Page、DocPerm、服务端授权模型并存且漂移。授权服务的 Manager/Operator 模型是正确方向，但历史泛用角色仍进入 Page 或获得写入权限。需要一份可执行的角色矩阵和 CI metadata 检查。

3. 草稿、已提交与文本状态混用。OIL-002 表明自定义 `status` 不能替代 `docstatus`。所有财务、库存、凭证和封账链必须以标准生命周期和不可变审计事件为核心。

4. 共享页面存在 SPA 生命周期债务。工作台实例按 wrapper 缓存的设计良好，但 document 级监听若不释放，页面返回次数越多，重复请求越可能增长。

5. UI Kit 具备入口但存量样式未收敛。样式门禁已经防止增量变坏，下一阶段需要将 1,572 个内联样式作为明确债务而不是“已通过”的替代指标。

6. 响应式、可访问性、冻结宽表和性能不能以源码替代实测。没有可用站点前，不应对滚动、焦点、读屏、视口裁切、Console 0 error 或 Network 0 failure 作任何通过性表述。

## 五、整改路线图

### 5.1 立即处理的 P0/P1

| 优先级 | 工作项 | 影响范围 | 回归风险 | 验收方法 |
|---|---|---|---|---|
| P0 | 修复 OIL-001 的真实 Document 绑定、事务内重算与审计 | 油卡删除、余额、台账 | 高 | 双卡/双公司删除负向测试；四柱守恒复算。 |
| P0 | 统一油卡可提交记录生命周期 | 充值、加油、锁定、报表 | 高 | 草稿/提交/取消/回滚状态及余额全链回归。 |
| P0 | 收口物业月结、租约发票和解锁服务 | 物业、租赁、封账 | 高 | 角色×公司×状态 API 矩阵和解锁审计检查。 |
| P0 | 保护税局原始发票附件 | 税局发票、File、归档 | 高 | 未授权删除/替换必拒绝；归档与恢复演练。 |
| P1 | 解决仓库反向公司校验与出库 HTML 转义 | 库存读取和前端详情 | 中高 | 多公司仓库负向测试、隔离环境 XSS 回归。 |
| P1 | 将 37 个写入 RPC 全部限定为 POST | 跨模块接口 | 中 | API 方法矩阵、CSRF、幂等和失败回滚测试。 |
| P1 | 对齐 Page、DocPerm、服务授权角色 | 所有自定义模块 | 高 | 角色矩阵自动化；只允许规定管理员/操作员对。 |

### 5.2 低风险快速修正

- 清理未经批准的装饰性图符文本，并复核所有提示语的中文业务语义。
- 将固定历史账期默认值替换为必填的动态期间参数；固定公司专属工作台由业务负责人确认后再保留或改造。
- 为高频新建弹窗增加一致的本地草稿保护和提交后清理逻辑。

### 5.3 共享组件与架构治理

- 建立服务端“真实资源授权”基础函数，统一 company、Document、docstatus、关联单据和动作权限校验。
- 为共享工作台补充 dispose/destroy 生命周期、请求代次控制和网络计数测试。
- 将内联样式基线改为逐模块递减目标；优先抽取宽表、弹窗、金额单元格、状态、建议浮层样式到 UI Kit。
- 建立 UI surface registry：从 hooks、Page、Workspace、Report、DocType JS 自动生成清单，并要求每项有对应角色、写入风险和 Playwright 场景。

### 5.4 需要业务负责人确认的规则

- 油卡充值/加油是否允许“提交即过账”，以及由何角色执行。
- 原始发票 PDF 的法定保留策略、删除是否一律禁止、可否由归档替代。
- 固定公司薪酬工作台是否为批准的业务边界；即使保留，期间仍必须动态。
- 物业月结的操作员是否可以草稿保存、谁可以核定、谁可解锁及所需理由。

### 5.5 暂不建议改动的部分

- 不建议在未获得业务授权前，把所有审批、付款、税务和封账操作一律改为“直接提交”。这些场景应先确认状态机与职责分离。
- 不建议为了缓解性能问题直接移除磨砂、渐变或投影。应先通过生命周期解绑、请求消重和局部渲染消除根因。
- 不建议仅凭静态检查结果调整宽表冻结、响应式或键盘行为；必须先恢复安全的 Playwright 验收条件。

## 六、证据附录

### 6.1 Playwright 场景与结果

| 场景 | 计划覆盖 | 结果 | 说明 |
|---|---|---|---|
| 冷启动、返回 Page、正常/空/错误状态 | 所有高风险 Page | 阻塞 | 登录页连接超时。 |
| 筛选、搜索、期间切换、弹窗草稿 | 所有含快捷操作 Page | 阻塞 | 无已授权会话；未写业务数据。 |
| 管理员/操作员/无权角色与多公司 | 角色敏感 Page | 阻塞 | 未取得测试账号或获批测试记录。 |
| 1920×1080、1366×768、约 900px | 所有高风险 Page | 阻塞 | 无可加载页面。 |
| Console、Network、截图 | 所有高风险 Page | 阻塞 | 无应用 DOM，截图索引为空。 |

### 6.2 Console、网络和截图索引

- 非预期 Console Error：未采集，不能记为 0。
- 非预期 Network failure：未采集，不能记为 0。
- 已知环境基线问题：仅观察到登录页连接超时；未能判断其是否为站点、网络、认证或浏览器会话问题。
- 截图：0 张。为避免敏感数据泄露，未保存任何页面截图或业务数据。

### 6.3 UI 样式治理检查结果

执行命令：`python scripts/verify_ui_style_governance.py`（仅检查）。

结果：`Inline styles: 1572 (baseline ceiling: 1588)`；脚本返回通过，含义是本次工作树没有新增内联样式，不能据此得出存量设计债务已消除的结论。

### 6.4 运行时恢复后必须补做的验收

1. 为每一个 1.2 中 Desk Page 建立最小读场景；为每一个写入 Page 建立隔离测试公司和可回收测试记录。
2. 对所有 P0/P1 先运行直接 RPC 的正负向角色测试，再运行真实 UI 流程，二者均通过才关闭风险。
3. 对宽表执行冻结列、表头、主体、横向滚动条同步测试；对弹窗执行静态背景、双关闭路径、草稿恢复、Esc、Tab、Ctrl/Cmd+S 与 focus-visible 测试。
4. 连续执行 A→B→A 20 次，记录请求数、Console、网络失败、事件监听数量和 DOM 实例数量。
5. 运行时报告只能使用脱敏的测试公司、测试编号和截图；不得附员工、工资、身份证、Token 或真实原始凭证。

### 6.5 官方资料

- Frappe Controller 生命周期：<https://docs.frappe.io/framework/user/en/basics/doctypes/controllers>
- Frappe 权限模型：<https://docs.frappe.io/framework/user/en/basics/users-and-permissions>

这些资料仅用于解释框架生命周期与权限语义；本报告的项目结论以实际应用源码、metadata 与本次运行状态为先。

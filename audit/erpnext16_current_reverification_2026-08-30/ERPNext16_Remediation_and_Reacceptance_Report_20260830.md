# ERPNext 16 自定义模块复核修复与实机再验收报告

日期：2026-08-30  
范围：薪酬、油卡与车辆、材料出库、物业租赁、税务发票、环保合规、特种设备及公共 UI 组件。  
约束：未创建、提交、取消、删除或导入任何真实业务单据；未执行 Git 提交或推送。

## 结论

本轮以当前源码和 `http://192.168.8.11:6888` 的实际 Desk 为准，未直接沿用历史报告结论。没有发现已确认的 P0。历史复核中确认的 P1 安全、动态数据边界和运行错误已完成修复并部署；仍保留 3 项 P2，包括遗留 UI 治理债务、缺少专用测试账号的权限负向验收，以及未完成全部宽表视口截图回归。

| 级别 | 已修复 | 仍待处理 |
| --- | ---: | ---: |
| P0 | 0 | 0 |
| P1 | 7 | 0 |
| P2 | 2 | 3 |

## P1 已修复项

### P1-01：薪酬、物业的页面、DocType 和服务端权限模型不一致

**实际证据**

- `Payroll Manager` / `Payroll Operator` 已写入薪酬工作台和三个核心薪酬 DocType；`Property Manager` 已补入费率和表计主数据权限。
- 运行端执行 `get_module_company_options(module="payroll")` 成功返回当前管理员可用的两家公司；薪酬 Desk 实机显示“核算公司”下拉，且控制台错误为 0。
- 旧“吉众”薪酬页已重定向到统一动态工作台，侧栏只保留一个入口，避免同一业务由两套权限和数据上下文处理。

**影响范围**

薪酬、物业的管理员和操作员入口、主数据维护、公司选择和结算读取。

**涉及文件**

- `ashan_cn_procurement/ashan_cn_procurement/services/authorization_service.py`
- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/page/qifu_hr_salary_workbench/`
- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/page/jizhong_hr_salary_workbench/`
- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/doctype/ashan_*payroll*/`
- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/doctype/property_charge_rate/`
- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/doctype/utility_meter/`

**复现步骤**

1. 以已登录 Desk 打开 `/desk/qifu-hr-salary-workbench`。
2. 检查“核算公司”下拉和两个授权公司选项；切换时不保存任何数据。
3. 打开 `/desk/jizhong-hr-salary-workbench`，确认自动跳转到统一薪酬工作台。

**修复建议**

继续在隔离环境用仅 Payroll Operator、仅 Property Operator 和无关角色账号执行 Page、DocType、RPC 三层负向回归。

### P1-02：薪酬首屏在公司上下文初始化前发起请求

**实际证据**

- 统一入口首次验收曾记录 3 条“必须指定薪酬核算公司”错误，来源为员工、工作流和重算状态请求。
- 已在 `load_qifu_employees()`、`load_monthly_workflow_hub()`、`load_calculation_center()`、轮询和 `refresh_workbench()` 增加空公司短路，仅在授权公司加载完成后发起请求。
- 最终 Desk 复验：页面标题为“人事薪酬工作台”，动态公司选择器可见，Console error 数量为 0。

**影响范围**

薪酬工作台首屏、SPA 回显、重算状态轮询和旧书签重定向。

**涉及文件**

- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/page/qifu_hr_salary_workbench/qifu_hr_salary_workbench.js`

**复现步骤**

1. 刷新 `/desk/qifu-hr-salary-workbench`。
2. 等待公司下拉渲染后检查浏览器 Console。
3. 预期不再出现“必须指定公司”或 Socket.IO `Invalid origin` 错误。

**修复建议**

后续把页面初始化改为显式 Promise 链，并为首屏请求补充 Playwright 断言，防止异步竞态回归。

### P1-03：材料出库接口绕过标准单据创建、删除和取消权限

**实际证据**

- 创建路径改为 `frappe.has_permission("Stock Entry", "create", throw=True)` 和普通 `doc.insert()`。
- 草稿撤回使用 `doc.check_permission("delete")`；已提交单据使用 `doc.check_permission("cancel")`，明细读取也先检查 read 权限。

**影响范围**

材料出库草稿创建、撤回、作废和只读详情。

**涉及文件**

- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/page/stock_issue_workbench/stock_issue_workbench.py`
- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/page/stock_issue_workbench/stock_issue_workbench.json`

**复现步骤**

1. 在隔离站点使用没有 Stock Entry create/delete/cancel 权限的账号调用对应 RPC。
2. 预期分别返回标准 Frappe 权限拒绝。
3. 使用有权限的测试账号创建可回收草稿并验证撤回权限，不对真实单据执行操作。

**修复建议**

补充 Stock Entry create/delete/cancel 的接口级自动化测试，并覆盖跨公司仓库参数。

### P1-04：物业月结使用固定单价、税率、主体和虚构附加收费

**实际证据**

- `Property Charge Rate` 现维护物业主体、电水含税单价和税率；生成月结时按租约、表计、有效期读取并保存快照，配置缺失或同月冲突会阻断。
- 前端、服务端导出均删除 `1.1957`、`5.5`、`13%`、`9%` 和三项附加收费常量的回退；仅展示当期已配置税率，未配置附加收费不再被推算。
- 实机物业月结页显示 `¥` 千分位金额、`kWh`/`m³` 单位、按公司正负调配和“按公司、费用类型与当期税率分组”的汇总表头。

**影响范围**

物业月结、抄表、导出、公司间调配和历史快照。

**涉及文件**

- `ashan_cn_procurement/ashan_cn_procurement/services/property_settlement.py`
- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/doctype/property_charge_rate/property_charge_rate.json`
- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/page/property_settlement_workbench/property_settlement_workbench.js`
- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/doctype/property_monthly_settlement/property_monthly_settlement.json`

**复现步骤**

1. 在隔离公司配置一条新的有效费率，不创建结算单。
2. 以只读方式加载该月物业工作台数据。
3. 检查价格、税率、物业主体和导出拆分是否等于配置快照，而非源码常量。

**修复建议**

后续增加“有效期重叠”和“电水表跨租约”两组无写入服务测试。

### P1-05：税票购买方白名单和公司归属存在硬编码与空公司风险

**实际证据**

- 购买方允许范围改为只读取 `Tax Invoice Settings.company_mappings` 的精确、已配置映射。
- 导入时不能映射公司即进入错误日志和待复核计数，不创建 company 为空的 Tax Invoice；`Tax Invoice.company` 改为必填。
- 运行端只读健康检查成功返回当前配置的购买方映射。

**影响范围**

税票导入、红蓝票匹配、公司筛选和后续统计。

**涉及文件**

- `ashan_cn_procurement/ashan_cn_procurement/services/tax_invoice_validation.py`
- `ashan_cn_procurement/ashan_cn_procurement/services/tax_invoice_import.py`
- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/doctype/tax_invoice/tax_invoice.json`
- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/doctype/tax_invoice_company_mapping/tax_invoice_company_mapping.json`

**复现步骤**

1. 在隔离站点配置新的公司与精确购买方映射。
2. 导入测试凭证；映射成功时只能创建带公司归属的记录。
3. 对未映射购买方执行同样操作；预期无 Tax Invoice 写入，仅产生待复核日志。

**修复建议**

为映射增加税号和有效期的唯一性校验，并加入未映射导入的自动化测试。

### P1-06：油卡锁定月份仍允许视觉点击，明文卡号从详情接口返回

**实际证据**

- 已锁定月份的“录入加油”“录入充值”在 Desk DOM 中均为 `disabled`；台账卡片和详情仅显示脱敏卡号。
- 实机油卡页的首行期初、期间发生、期末结存和合计行完整显示，控制台 error 为 0。

**影响范围**

油卡录入防误操作、卡号最小暴露和四柱余额闭环。

**涉及文件**

- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/page/oil_card_ledger/oil_card_ledger.js`
- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/page/oil_card_ledger/oil_card_ledger.py`
- `ashan_cn_procurement/ashan_cn_procurement/public/css/ashan_ui_kit.css`

**复现步骤**

1. 打开已核定月份的 `/desk/oil-card-ledger`。
2. 检查两个录入按钮的 `disabled` 和 `aria-disabled` 状态，不点击、不填写。
3. 检查页面和响应中的卡号只保留掩码。

**修复建议**

如果确需展示完整卡号，应建立仅 Oil Card Manager 可用、需填写原因并留审计记录的短时揭示接口。

### P1-07：按 IP 访问 Desk 时 Socket.IO Origin 不匹配

**实际证据**

- Nginx Socket.IO 代理已将 Origin 和 Host 转发为 `$scheme://$http_host` 与 `$http_host`，保留 Frappe 站点名路由。
- 配置经 `nginx -t` 验证后热重载；最终油卡和薪酬页面 Console error 均为 0。

**影响范围**

Desk 实时通知、事件推送、局部刷新和所有依赖 Socket.IO 的自定义页面。

**涉及文件**

- `scripts/sync_and_migrate.py`
- 测试容器 `/etc/nginx/conf.d/frappe.conf` 的 Socket.IO location。

**复现步骤**

1. 以 `http://192.168.8.11:6888` 打开油卡或薪酬页面。
2. 检查 Console 是否存在 `Invalid origin`。
3. 预期为 0 条该错误。

**修复建议**

将该 Nginx 规则固化进容器镜像或部署模板，避免容器重建后丢失运行配置。

## P2 已修复项

### P2-01：合同工作台 SPA 回显与新建草稿恢复缺失

**实际证据**

- 合同工作台已增加 `on_page_show` 局部刷新。
- 新建合同支持 localStorage 草稿恢复，取消/关闭不丢失已录入字段，成功创建后清除；删除了固定金额和 20/30/50 分期预置。

**影响范围**

合同高频录入、Desk SPA 返回和误关闭恢复。

**涉及文件**

- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/page/contract_workbench/contract_workbench.js`

**复现步骤**

1. 在隔离环境打开新建合同弹窗并填写非敏感测试字段。
2. 关闭后重新打开，检查草稿恢复；不点击保存。
3. 在其他页面返回合同工作台，检查列表是否局部刷新。

**修复建议**

为草稿加过期时间和账号/公司作用域，避免共享终端串用。

### P2-02：薪酬旧入口导致视觉与操作逻辑重复

**实际证据**

- 侧栏从两条按公司命名的工作台入口收敛为“人事薪酬工作台”。
- 旧吉众 URL 实机跳转至动态薪酬页，页面标题统一为“人事薪酬工作台”。

**影响范围**

Desk 导航一致性、公司切换认知和维护成本。

**涉及文件**

- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/workspace_sidebar/home.json`
- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/page/jizhong_hr_salary_workbench/`

**复现步骤**

1. 打开 `/desk/jizhong-hr-salary-workbench`。
2. 检查地址自动变为 `/desk/qifu-hr-salary-workbench`，页面使用公司下拉而非固定主体。

**修复建议**

后续可在发布窗口将遗留 Page 标记为废弃，并为已保存书签提供一次性迁移提示。

## P2 待处理项

### P2-03：遗留页面尚未完成全量 UI 令牌化和零图形文字治理

**实际证据**

- 样式治理通过，但当前仍有 1,565 处遗留 `style=`；工资、物业、油卡、税票、环保和特种设备页面还存在历史图形文字和不完全统一的表头结构。
- 本轮未新增内联样式，计数已由复核时的 1,570 降至 1,565。

**影响范围**

跨模块视觉语言、可维护性、宽表可读性和无图形文字规范。

**涉及文件**

- `ashan_cn_procurement/ashan_cn_procurement/public/css/ashan_ui_kit.css`
- `ashan_cn_procurement/ashan_cn_procurement/ashan_cn_procurement/page/*/*.js`

**复现步骤**

1. 并排打开薪酬、物业、油卡、税票、环保和特种设备页面。
2. 比较表头、按钮、状态图形文字和冻结列样式。
3. 运行 `python scripts/verify_ui_style_governance.py` 查看遗留计数。

**修复建议**

按工作台逐批将内联样式迁移到 `ashan_ui_kit.css`，先处理可见的表头、状态、金额、按钮和弹窗；每批只减不增，并增加 1280px 与窄屏截图回归。

### P2-04：管理员、操作员、无关角色和跨公司用户的真实负向验证未完成

**实际证据**

- 本轮仅使用现有管理员 Desk 会话；不能创建真实业务单据，也未获得专用的角色测试账号。
- 代码和 Page/DocType 配置已收敛，但“拒绝”行为没有以独立账号进行真实 HTTP/Desk 验收。

**影响范围**

薪酬、物业、油卡、税票、合规、特种设备和材料出库的最终权限交付信心。

**涉及文件**

- `services/authorization_service.py`
- 各模块 Page JSON、DocType JSON 和写入 RPC。

**复现步骤**

1. 在隔离站点准备管理员、操作员、无关角色和单公司/跨公司账号。
2. 对每个模块验证页面可见、读取、创建、提交、取消、删除与跨公司查询。
3. 使用可回收测试单据进行正向和拒绝回归。

**修复建议**

提供隔离公司和上述账号后，补充 Playwright 多会话权限矩阵；测试单据应带固定测试前缀并在用户授权后统一清理。

### P2-05：全部宽表视口、冻结列和网络响应未完成全量截图回归

**实际证据**

- 本轮已用 Playwright 实机打开物业、油卡、薪酬和旧入口重定向，检查表格、禁用态、公司选择和 Console；未对所有宽表在多个视口保存完整截图，也未获得浏览器网络追踪接口。

**影响范围**

大宽表横向滚动、冻结列、弹窗边界和慢网络状态下的视觉稳定性。

**涉及文件**

- 各工作台 Page JavaScript 和 `public/css/ashan_ui_kit.css`。

**复现步骤**

1. 在 1280px、1440px 和窄屏视口依次打开薪酬、库存、物业、油卡、税票、环保和特种设备。
2. 横向滚动每张大表，检查表头、首列和合计行的对齐。
3. 检查页面加载、筛选、只读弹窗和 Console/Network。

**修复建议**

建立不写入业务数据的 Playwright 截图基线和控制台断言；对提交等写操作仅在隔离站点执行。

## 部署与验证记录

- Python AST、JavaScript 语法、DocType/Workspace JSON 和 `git diff --check` 已通过。
- `python scripts/verify_ui_style_governance.py` 通过，遗留内联样式 1,565，基线上限 1,588。
- 自定义应用已同步至测试容器；站点迁移进程完成、前端构建成功、缓存已清理、容器已重启并恢复健康。
- 没有执行 Git commit 或 push。

# ERPNext 16 采购与侧边栏 V2 完整整合包

基线：`v1.0.0-milestone-payroll-core`

本目录不是“替换文件包”，而是已经把采购/库存/销售侧边栏 V2 修改直接合入后的**完整项目源码**。

## 已整合

- 左侧业务菜单补齐：采购与供应链、仓库与库存、销售与出库、财税与发票、人事薪酬、物业租赁、车辆油卡、企业合规。
- `workspace_sidebar/home.json` 作为统一业务菜单模板，继续由现有 `setup.sync_all_workspace_sidebars()` 在 migrate 时同步。
- 新增 `/desk/procurement-workflow`：采购申请 → 采购订单 → 采购入库 → 采购发票 → 报销/付款的只读流程总览。
- 重做 `Procurement Management` Workspace，采购链路按顺序排列。
- 新增 `ashan_cn_sidebar_v2.js`，停止全局加载旧 sidebar JS。
- Purchase Invoice / Reimbursement Request 表单 JS 改为 DocType 级加载，避免重复注册。
- 修复服务端登录路由：Purchase / Stock / Accounts 用户不再被默认送到油卡页面；角色路由与 Sidebar V2 保持一致。
- 修复 Sidebar V2 重复绑定 router change 事件的问题。
- 未知/其他 App 的 Sidebar 解析不再被强行接管到 My Business。
- 纯油卡操作员直接访问 Home/My Business 时仍会回到油卡工作台。
- 新增基础导航回归测试 `test_business_navigation_v2.py`。
- 从交付 ZIP 中清理 `__pycache__` / `*.pyc`，源码行为不受影响。

## 静态检查

已执行：

- 整个 `ashan_cn_procurement` Python `compileall`：PASS
- 项目全部 104 个 JSON 解析：PASS
- App 全部 78 个 JavaScript `node --check`：PASS
- Purchase Invoice / Reimbursement Request 脚本重复加载检查：PASS
- 侧边栏所有自定义 Page 目标源码存在性检查：PASS

本环境没有你的 ERPNext 16 运行实例，因此以下必须在测试站点执行：

```bash
bench --site <site> migrate
bench build --app ashan_cn_procurement
bench --site <site> clear-cache
bench restart
```

然后重点验证首次登录、左侧菜单、`/desk/procurement-workflow`、Material Request / Purchase Order / Purchase Receipt / Purchase Invoice 切换以及油卡角色。

## 本版没有继续动的高风险财务逻辑

- `purchase_invoice_tax.py` 对 ERPNext 核心金额字段的覆盖逻辑；
- Reimbursement Request Submit / Cancel 生命周期；
- Payment Entry 与报销支付状态联动；
- 两个当前空壳的报销报表。

这些应作为下一阶段单独财务正确性补丁并进行真实会计回归，不建议和导航重构混在一次上线。

## 重要：完整包保留了基线原有数据

这是基于你上传的完整 milestone 源码直接整合的，所以**仍保留基线中原本存在的真实人事/工资 seed / historical data 文件**。该 ZIP 适合你本地/私有环境部署验证，但在未完成脱敏和 Git 历史清理前，不应再次公开发布。

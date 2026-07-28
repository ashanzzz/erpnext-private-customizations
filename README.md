# ERPNext 16 项目环境与 `ashan_cn_procurement` App 目录

本项目包含了 **ERPNext 16 本地环境配置** 以及从远程站点完整的 **`ashan_cn_procurement` (业务扩展 App)** 源码规范结构。

---

## 📁 目录结构

```text
erpnext16/
├── .env                       # 本地凭据配置 (站点 URL、Token、App 名等)
├── .env.example               # 配置模板 (脱敏，提交版本库)
├── .gitignore                 # 忽略敏感文件 (.env)
├── README.md                  # 本说明文档
└── ashan_cn_procurement/      # 核心 App 模块 (业务扩展)
    ├── pyproject.toml         # Python App 包元数据
    └── ashan_cn_procurement/
        ├── __init__.py
        ├── hooks.py           # Frappe App 钩子与扩展注册
        ├── modules.txt        # 模块声明 (Ashan CN Procurement)
        ├── doctype/           # 14 个 DocType 单据模型
        │   ├── compliance_equipment_item/
        │   ├── employee_certificate_item/
        │   ├── environmental_compliance_item/
        │   ├── oil_card/                           # 油卡模型
        │   ├── oil_card_invoice_batch/
        │   ├── oil_card_invoice_batch_item/
        │   ├── oil_card_recharge/                  # 油卡充值
        │   ├── oil_card_refuel_log/                # 加油记录
        │   ├── reimbursement_invoice_item/
        │   ├── reimbursement_request/              # 报销申请
        │   ├── restricted_access_group/            # 权限限制组
        │   ├── restricted_access_group_role/
        │   ├── restricted_access_group_user/
        │   └── vehicle_fuel_settings/
        └── report/            # 14 个报表模板
            ├── company_compliance_overview/
            ├── oil_card_balance_reconciliation/
            ├── oil_card_monthly_ledger/
            ├── vehicle_fuel_cost_summary/
            └── ...
```

---

## 🎓 ERPNext 16 App 开发与二次开发核心知识

在 Frappe / ERPNext 16 框架中，开发 App 遵循以下核心规范：

### 1. DocType 单据结构
每个 DocType 对应一个独立目录，包含三个核心文件：
- **`<doctype_name>.json`**: 模型元数据定义（包含字段 List、字段类型 FieldType、权限 Permissions 等）。
- **`<doctype_name>.py`**: 后端 Python 控制器逻辑类，继承自 `frappe.model.document.Document`，可编写 `validate`, `on_submit`, `on_cancel` 等钩子。
- **`<doctype_name>.js`**: 前端 Form 表单 JS 交互逻辑（使用 `frappe.ui.form.on('<DocType Name>', { ... })`）。

### 2. 开发者模式 (Developer Mode)
- 远程/标准应用在没有启用 `developer_mode: 1`（在 `site_config.json` 中配置）时，标准单据禁止直接通过前端接口更改模型定义。
- 本地进行 App 开发时，编辑 `<doctype_name>.json` 和 `<doctype_name>.py` 更改字段和业务逻辑，然后通过 Git/Bench 同步到服务器端。

### 3. Hooks (`hooks.py`)
- 用于向 ERPNext 核心逻辑插桩（例如监听 `doc_events`，扩展 `override_doctype_class`，或嵌入自定义静态资源/页面）。

---

## 🛠️ 本地常用脚本

- **`inspect_app.py`**: 查询远程 ERPNext 站点上 App 的模块与单据状态。
- **`download_app_via_api.py`**: 从远程站点同步/导出最新的 DocType 与 Report 架构定义到本地。

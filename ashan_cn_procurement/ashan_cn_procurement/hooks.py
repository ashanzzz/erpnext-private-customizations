app_name = "ashan_cn_procurement"
app_title = "业务扩展"
app_publisher = "Ashan CN Procurement"
app_description = "ERPNext 16 采购、报销、油卡与受限单据业务扩展"
app_email = "dev@example.invalid"
app_license = "mit"

# Includes in <head>
# ------------------

app_include_css = [
    "/assets/ashan_cn_procurement/css/ashan_cn_procurement.css?v=20260824.06",
    # Versioned so Desk never keeps an obsolete global component definition
    # after a UI-kit deployment.  The file itself remains a shared static asset.
    "/assets/ashan_cn_procurement/css/ashan_ui_kit.css?v=20260824.06",
]

# 全局仅加载真正的全站能力。
# Purchase Invoice / Reimbursement Request 的脚本改为 doctype_js，
# 避免在全 Desk 重复注册表单事件。
app_include_js = [
    "/assets/ashan_cn_procurement/js/ashan_ui_kit.js",
    "/assets/ashan_cn_procurement/js/ashan_cn_translations.js",
    "/assets/ashan_cn_procurement/js/ashan_cn_sidebar_v2.js?v=20260824.06",
    "/assets/ashan_cn_procurement/js/doc_details_list.js",
]

# App Switcher Dropdown Registration (Frappe 16 Official Multi-App Standard)
add_to_apps_screen = [
    {
        "name": "ashan_cn_procurement",
        "title": "业务扩展",
        "route": "/desk/Workspaces/Home"
    }
]

# 首次登录路由保护（Frappe v16）：
# 保持里程碑已验证的三层登录路由方案，不在本次导航重构中改变。
website_redirects = [
    {
        "source": "/",
        "target": "/desk/Workspaces/Home",
        "redirect_http_status": 302,
    },
]

on_session_creation = "ashan_cn_procurement.boot.set_login_redirect"
get_website_user_home_page = "ashan_cn_procurement.boot.get_website_user_home_page"
extend_bootinfo = "ashan_cn_procurement.boot.boot_session"

role_home_page = {
    "System Manager": "desk/Workspaces/Home",
    "Administrator": "desk/Workspaces/Home",
    "Purchase User": "desk/Workspaces/Procurement Management",
    "Purchase Manager": "desk/Workspaces/Procurement Management",
    "Stock User": "desk/Workspaces/Stock and Inventory",
    "Stock Manager": "desk/Workspaces/Stock and Inventory",
    "Accounts User": "desk/Workspaces/Accounting and Finance",
    "Accounts Manager": "desk/Workspaces/Accounting and Finance",
    "Oil Card Operator": "desk/oil-card-ledger",
    "Oil Card Manager": "desk/oil-card-ledger",
    "油卡操作员": "desk/oil-card-ledger",
    "油卡管理员": "desk/oil-card-ledger",
    "All": "desk/Workspaces/Home",
}

# DocType Specific Client Scripts
doctype_js = {
    "Purchase Invoice": "public/js/purchase_invoice_tax_calculator.js",
    "Reimbursement Request": "public/js/reimbursement_request.js",
    "Vehicle": "public/js/vehicle_custom.js",
}

doctype_list_js = {
    "Material Request": "public/js/material_request_list.js",
    "Purchase Order": "public/js/purchase_order_list.js",
    "Purchase Receipt": "public/js/purchase_receipt_list.js",
    "Purchase Invoice": "public/js/purchase_invoice_list.js",
    "Reimbursement Request": "public/js/reimbursement_request_list.js"
}

# Doc Events / Server Hooks
doc_events = {
    "Material Request": {
        "validate": "ashan_cn_procurement.overrides.document_details.update_doc_details"
    },
    "Purchase Order": {
        "validate": "ashan_cn_procurement.overrides.document_details.update_doc_details"
    },
    "Purchase Receipt": {
        "validate": "ashan_cn_procurement.overrides.document_details.update_doc_details"
    },
    "Purchase Invoice": {
        "before_validate": [
            "ashan_cn_procurement.overrides.purchase_invoice_tax.calculate_china_line_taxes",
            "ashan_cn_procurement.overrides.document_details.update_doc_details"
        ],
        "validate": "ashan_cn_procurement.overrides.purchase_invoice_tax.validate_purchase_invoice_taxes",
        "after_insert": "ashan_cn_procurement.services.tax_invoice_matcher.on_purchase_invoice_change",
        "on_update": "ashan_cn_procurement.services.tax_invoice_matcher.on_purchase_invoice_change",
        "on_update_after_submit": "ashan_cn_procurement.services.tax_invoice_matcher.on_purchase_invoice_change",
        "on_cancel": "ashan_cn_procurement.services.tax_invoice_matcher.on_purchase_invoice_change",
        "on_trash": "ashan_cn_procurement.services.tax_invoice_matcher.on_purchase_invoice_delete"
    },
    "Reimbursement Request": {
        "validate": "ashan_cn_procurement.overrides.document_details.update_doc_details"
    },
    "Vehicle": {
        "on_update": "ashan_cn_procurement.overrides.vehicle_sync.on_vehicle_update"
    }
}

# Scheduled Tasks
scheduler_events = {
    "daily": [
        "ashan_cn_procurement.services.special_equipment.refresh_all_special_equipment_status",
        "ashan_cn_procurement.services.environmental_management.refresh_all_environmental_status",
        "ashan_cn_procurement.services.tax_invoice_cleanup.cleanup_expired_tax_invoice_pdfs",
        "ashan_cn_procurement.services.tax_invoice_matcher.reconcile_tax_invoice_matches"
    ]
}

# Post-Migration Hooks
# 仍沿用当前 setup.after_migrate；该函数会读取 workspace_sidebar/home.json
# 并同步所有业务 Sidebar。本版本把 home.json 升级为唯一完整菜单模板。
after_migrate = "ashan_cn_procurement.setup.after_migrate"

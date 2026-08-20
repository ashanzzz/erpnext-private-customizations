app_name = "ashan_cn_procurement"
app_title = "业务扩展"
app_publisher = "Ashan CN Procurement"
app_description = "ERPNext 16 采购、报销、油卡与受限单据业务扩展"
app_email = "ashanzzz1213@gmail.com"
app_license = "mit"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = [
    "/assets/ashan_cn_procurement/css/ashan_cn_procurement.css",
    "/assets/ashan_cn_procurement/css/ashan_ui_kit.css",
]
app_include_js = [
    "/assets/ashan_cn_procurement/js/ashan_ui_kit.js",
    "/assets/ashan_cn_procurement/js/ashan_cn_translations.js",
    "/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js",
    "/assets/ashan_cn_procurement/js/purchase_invoice_tax_calculator.js",
    "/assets/ashan_cn_procurement/js/reimbursement_request.js",
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
# 用户从站点根地址 `/` 登录时，官方 login.js 会优先使用 URL 中的
# `redirect-to=/`，覆盖登录接口返回的 `home_page`。登录后回到空路由，Desk
# 就会按 bootinfo.home_page 渲染官方 desktop/App 选择页。必须在 Website Path
# Resolver 阶段把根地址先送到真实 Workspace，不能改回仅靠前端 set_route。
# 注意：website_redirects 不处理已被 Desk renderer 接管的 `/desk`；该路径仍由
# ashan_cn_sidebar.js 的路由守卫兜底。这里专门修复用户报告的“从 `/` 首次登录”。
website_redirects = [
    {
        "source": "/",
        "target": "/desk/Workspaces/Home",
        "redirect_http_status": 302,
    },
]

# Post-Login Default Page (Dashboard / Workspace)
on_session_creation = "ashan_cn_procurement.boot.set_login_redirect"
get_website_user_home_page = "ashan_cn_procurement.boot.get_website_user_home_page"
extend_bootinfo = "ashan_cn_procurement.boot.boot_session"

# role_home_page 是 get_website_user_home_page 未返回值时的网站层回退配置。
# 本项目的显式 get_website_user_home_page hook 优先级更高；这里仍保持同一目标，
# 防止未来调整 hook 时管理员重新落到空 `/desk` 路由。
role_home_page = {
    "System Manager": "desk/Workspaces/Home",
    "Administrator": "desk/Workspaces/Home",
    "Oil Card Operator": "desk/oil-card-ledger",
    "Oil Card Manager": "desk/oil-card-ledger",
    "油卡操作员": "desk/oil-card-ledger",
    "油卡管理员": "desk/oil-card-ledger",
    "Stock User": "desk/stock-entry",
    "Stock Manager": "desk/stock-entry",
    "Purchase User": "desk/purchase-order",
    "Purchase Manager": "desk/purchase-order",
    "Accounts User": "desk/reimbursement-request",
    "Accounts Manager": "desk/reimbursement-request",
    "All": "desk/oil-card-ledger"
}

# DocType Specific Client Scripts
doctype_js = {
    "Purchase Invoice": "public/js/purchase_invoice_tax_calculator.js",
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



# Scheduled Tasks (Daily Expiry & Reminder Refresh & Tax Invoice Lifecycle)
scheduler_events = {
    "daily": [
        "ashan_cn_procurement.services.special_equipment.refresh_all_special_equipment_status",
        "ashan_cn_procurement.services.environmental_management.refresh_all_environmental_status",
        "ashan_cn_procurement.services.tax_invoice_cleanup.cleanup_expired_tax_invoice_pdfs",
        "ashan_cn_procurement.services.tax_invoice_matcher.reconcile_tax_invoice_matches"
    ]
}

# Post-Migration Hooks
after_migrate = "ashan_cn_procurement.setup.after_migrate"

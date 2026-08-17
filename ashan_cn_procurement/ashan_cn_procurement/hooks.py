app_name = "ashan_cn_procurement"
app_title = "业务扩展"
app_publisher = "Ashan CN Procurement"
app_description = "ERPNext 16 采购、报销、油卡与受限单据业务扩展"
app_email = "ashanzzz1213@gmail.com"
app_license = "mit"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/ashan_cn_procurement/css/ashan_cn_procurement.css"
app_include_js = [
    "/assets/ashan_cn_procurement/js/ashan_cn_translations.js",
    "/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js",
    "/assets/ashan_cn_procurement/js/purchase_invoice_tax_calculator.js",
    "/assets/ashan_cn_procurement/js/reimbursement_request.js",
]

# App Switcher Dropdown Registration
add_to_apps_screen = [
    {
        "name": "ashan_cn_procurement",
        "title": "业务扩展",
        "route": "/desk/my-business"
    }
]

# Post-Login Default Page (Dashboard / Workspace)
on_session_creation = "ashan_cn_procurement.boot.set_login_redirect"
get_website_user_home_page = "ashan_cn_procurement.boot.get_website_user_home_page"
extend_bootinfo = "ashan_cn_procurement.boot.boot_session"

role_home_page = {
    "System Manager": "desk/my-business",
    "Administrator": "desk/my-business",
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
    "Purchase Invoice": "public/js/purchase_invoice_list.js"
}

# Doc Events / Server Hooks
doc_events = {
    "Purchase Invoice": {
        "before_validate": "ashan_cn_procurement.overrides.purchase_invoice_tax.calculate_china_line_taxes",
        "validate": "ashan_cn_procurement.overrides.purchase_invoice_tax.validate_purchase_invoice_taxes"
    },
    "Vehicle": {
        "on_update": "ashan_cn_procurement.overrides.vehicle_sync.on_vehicle_update"
    }
}


# Scheduled Tasks (Daily Expiry & Reminder Refresh)
scheduler_events = {
    "daily": [
        "ashan_cn_procurement.services.special_equipment.refresh_all_special_equipment_status",
        "ashan_cn_procurement.services.environmental_management.refresh_all_environmental_status"
    ]
}

# Post-Migration Hooks
after_migrate = "ashan_cn_procurement.setup.after_migrate"



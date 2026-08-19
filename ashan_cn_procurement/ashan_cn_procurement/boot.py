import os
import frappe


BUSINESS_SIDEBAR_NAMES = {
    "my business",
    "accounting and finance",
    "ashan cn procurement",
    "company compliance center",
    "procurement management",
    "property and lease",
    "stock and inventory",
    "vehicle fuel hub",
}
SYSTEM_MANAGEMENT_LABEL = "系统管理"
SYSTEM_MANAGEMENT_URLS = {
    "/desk/client-script",
    "/desk/customize-form/Customize%20Form",
    "/desk/server-script",
    "/desk/system-settings",
}


def set_login_redirect(*args, **kwargs):
    """
    Hook for on_session_creation.
    根据用户角色动态决定登录后跳转的目标首页
    """
    user = frappe.session.user
    roles = frappe.get_roles(user) if user else []
    if "System Manager" in roles or "Administrator" in roles:
        # 保持所有登录入口一致。若这里退回 /desk，某些非标准登录流程会先渲染
        # Frappe v16 的 desktop/App 选择页，再等待前端脚本补跳到 Workspace。
        home_route = "/desk/Workspaces/Home"
    elif any(r in roles for r in ["Oil Card Operator", "Oil Card Manager", "油卡操作员", "油卡管理员"]):
        home_route = "/desk/oil-card-ledger"
    elif any(r in roles for r in ["Stock User", "Stock Manager"]):
        home_route = "/desk/stock-entry"
    elif any(r in roles for r in ["Purchase User", "Purchase Manager"]):
        home_route = "/desk/purchase-order"
    else:
        home_route = "/desk/oil-card-ledger"

    for arg in args:
        if hasattr(arg, "home_page"):
            arg.home_page = home_route
    if hasattr(frappe.local, "login_manager") and frappe.local.login_manager:
        frappe.local.login_manager.home_page = home_route
    if hasattr(frappe, "local") and hasattr(frappe.local, "response"):
        frappe.local.response["home_page"] = home_route

def get_website_user_home_page(user):
    """
    Website hook: 返回无前导 '/' 的路径（框架会自动拼接 '/'）。
    Frappe v16 auth.py line 206:
        home_page = get_home_page() or '/desk'
    get_home_page() → get_home_page_via_hooks() → get_website_user_home_page()
    返回值直接作为 response['home_page']，浏览器跳转到此路径。

    对 System Manager / Administrator：直接跳到自定义首页 Workspace，
    避免先加载 desktop 再 JS 跳转导致侧边栏无法初始化的问题。
    """
    roles = frappe.get_roles(user) if user else []
    if "System Manager" in roles or "Administrator" in roles:
        # 直接让浏览器访问 Workspace 路由，侧边栏可正常初始化
        return "desk/Workspaces/Home"
    return "desk/oil-card-ledger"


def boot_session(bootinfo):
    """
    extend_bootinfo hook: 注入 bootinfo 字段。

    Frappe v16 pageview.js line 52:
        name = frappe.boot ? frappe.boot.home_page : window.page_name;
        frappe.views.pageview.with_page(name, ...)
    → home_page 必须是一个真实存在的 Frappe Page name。
    → 'desktop' 对应 tabPage 中 name='desktop' 的页面——这是 Frappe 原生大图标页。

    对于导航到我们自定义 Workspace 'Home'，则需要通过
    前端 JS (ashan_cn_sidebar.js) 在 Desk 加载完成后主动调用
    frappe.set_route(['Workspaces', 'Home']) 实现跳转。
    """
    user = frappe.session.user
    roles = frappe.get_roles(user) if user else []
    is_system_manager = "System Manager" in roles or "Administrator" in roles
    bootinfo.ashan_is_system_manager = is_system_manager

    if is_system_manager:
        # 'desktop' 是合法的 Frappe Page name。
        # 注意：这里不能写 "Workspaces/Home"，因为空路由时 pageview 会把
        # bootinfo.home_page 当成 DocType `Page` 的 name，而 Workspace 不是 Page。
        # 首次 HTTP 落地由 hooks.py 的 website_redirects 和上面的登录 hook 负责；
        # 此值只保留为异常情况下的合法 Page 回退，不能再作为首页跳转方案。
        bootinfo.home_page = "desktop"
    else:
        bootinfo.home_page = "oil-card-ledger"

    # 动态净化侧边栏并注入两页独立工作台项目
    for sidebar_name, sidebar in (bootinfo.get("workspace_sidebar_item") or {}).items():
        if isinstance(sidebar, dict) and "items" in sidebar:
            items = sidebar.get("items", [])
            new_items = []
            has_lease_bench = any("lease-settlement-workbench" in str(it.get("link_to", "")) or "lease-settlement-workbench" in str(it.get("url", "")) for it in items)

            for it in items:
                link_to = str(it.get("link_to", ""))
                url = str(it.get("url", ""))

                # 过滤已废弃的收费标准版本 (已与 Property Lease 合并)
                if link_to == "Property Charge Rate" or "property-charge-rate" in url or it.get("label") == "收费标准版本":
                    continue

                # 过滤系统管理
                if not is_system_manager and sidebar_name in BUSINESS_SIDEBAR_NAMES:
                    if it.get("label") == SYSTEM_MANAGEMENT_LABEL or url in SYSTEM_MANAGEMENT_URLS:
                        continue


                if "property-settlement-workbench" in link_to or "property-settlement-workbench" in url:
                    it["label"] = "水电费月结工作台"
                    new_items.append(it)
                    if not has_lease_bench:
                        new_items.append({
                            "label": "房租与物业费工作台",
                            "link_type": "Page",
                            "type": "Link",
                            "link_to": "lease-settlement-workbench",
                            "url": "/desk/lease-settlement-workbench",
                            "child": 1,
                            "collapsible": 0,
                            "indent": 0,
                            "keep_closed": 0,
                            "show_arrow": 0,
                            "doctype": "Workspace Sidebar Item"
                        })
                else:
                    new_items.append(it)
            sidebar["items"] = new_items

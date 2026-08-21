/* ==========================================================================
   ERPNext 16 业务扩展 - Sidebar V2
   Goals:
   1) Keep the business sidebar persistent on Buying/Stock/Accounts/Selling docs.
   2) Keep Frappe's native Section Break behavior; do not rewrite toggle/listener internals.
   3) Use role-aware root routing instead of sending unrelated users to oil-card-ledger.
   4) Keep the existing two-level visual hierarchy.
   ========================================================================== */

(function () {
    "use strict";

    const BUSINESS_SIDEBAR = "My Business";
    const BUSINESS_MODULES = new Set([
        "setup",
        "buying",
        "stock",
        "accounts",
        "selling",
        "hr",
        "ashan_cn_procurement",
        "ashan cn procurement",
    ]);

    const SECTION_ROUTES = {
        "我的业务 (总控主页)": ["Workspaces", "Home"],
        "采购与供应链": ["Workspaces", "Procurement Management"],
        "采购协同": ["Workspaces", "Procurement Management"],
        "仓库与库存": ["Workspaces", "Stock and Inventory"],
        "销售与出库": ["List", "Sales Order", "List"],
        "财税与发票中心": ["Workspaces", "Accounting and Finance"],
        // 当前仓库没有独立 HR Workspace；该一级标题仅使用 Frappe 原生展开/收起。
        "物业与租赁": ["Workspaces", "Property and Lease"],
        "车辆和车用油管理": ["Workspaces", "Vehicle Fuel Hub"],
        "企业合规中心": ["Workspaces", "Company Compliance Center"],
    };

    const OIL_OPERATOR_ROLES = ["Oil Card Operator", "油卡操作员"];
    const OIL_MANAGER_ROLES = [
        "System Manager",
        "Oil Card Manager",
        "油卡管理员",
        "Purchase Manager",
        "Accounts Manager",
        "Stock Manager",
    ];

    function getRoles() {
        if (!window.frappe) return [];
        if (frappe.boot && frappe.boot.user && Array.isArray(frappe.boot.user.roles)) {
            return frappe.boot.user.roles;
        }
        return Array.isArray(frappe.user_roles) ? frappe.user_roles : [];
    }

    function hasAnyRole(names) {
        const roles = getRoles();
        return names.some((name) => roles.includes(name));
    }

    function isAdministrator() {
        return Boolean(
            window.frappe &&
            frappe.session &&
            frappe.session.user === "Administrator"
        );
    }

    function isPureOilOperator() {
        return hasAnyRole(OIL_OPERATOR_ROLES) &&
            !hasAnyRole(OIL_MANAGER_ROLES) &&
            !isAdministrator();
    }

    function defaultRouteForUser() {
        if (isAdministrator() || hasAnyRole(["System Manager"])) {
            return ["Workspaces", "Home"];
        }
        if (hasAnyRole(["Purchase Manager", "Purchase User"])) {
            return ["Workspaces", "Procurement Management"];
        }
        if (hasAnyRole(["Stock Manager", "Stock User"])) {
            return ["Workspaces", "Stock and Inventory"];
        }
        if (hasAnyRole(["Accounts Manager", "Accounts User"])) {
            return ["Workspaces", "Accounting and Finance"];
        }
        if (hasAnyRole(["Oil Card Manager", "油卡管理员", "Oil Card Operator", "油卡操作员"])) {
            return ["oil-card-ledger"];
        }
        return ["Workspaces", "Home"];
    }

    function handleRootRoute() {
        if (!window.frappe || !frappe.get_route || !frappe.set_route) return;
        const route = frappe.get_route() || [];
        const joined = Array.isArray(route) ? route.join("/").toLowerCase() : "";

        const rootLike = (
            joined === "" ||
            joined === "desk" ||
            joined === "desktop" ||
            (route.length === 1 && ["desk", "desktop"].includes(String(route[0]).toLowerCase()))
        );

        const workspaceHomeLike = (
            joined === "workspaces/home" ||
            joined === "workspaces/my business" ||
            joined === "workspaces/my%20business"
        );

        if (isPureOilOperator() && (rootLike || workspaceHomeLike)) {
            frappe.set_route("oil-card-ledger");
            return;
        }

        if (rootLike) {
            frappe.set_route(...defaultRouteForUser());
        }
    }

    function patchSidebarResolver() {
        if (!window.frappe || !frappe.ui || !frappe.ui.Sidebar) return false;
        const Sidebar = frappe.ui.Sidebar;
        if (Sidebar._ashan_v2_resolver_patched) return true;

        const originalResolve = Sidebar.prototype.resolve_sidebar;
        Sidebar.prototype.resolve_sidebar = function (doctype, module) {
            const moduleLower = String(module || "").toLowerCase();
            if (!moduleLower || BUSINESS_MODULES.has(moduleLower)) {
                return BUSINESS_SIDEBAR;
            }
            return originalResolve
                ? originalResolve.apply(this, arguments)
                : null;
        };

        Sidebar._ashan_v2_resolver_patched = true;
        return true;
    }

    function injectStyles() {
        if (document.getElementById("ashan-sidebar-v2-style")) return;

        const style = document.createElement("style");
        style.id = "ashan-sidebar-v2-style";
        style.textContent = `
            .body-sidebar .section-item > .standard-sidebar-item .sidebar-item-label {
                font-weight: 700 !important;
                font-size: 13.5px !important;
            }
            .body-sidebar .section-item > .standard-sidebar-item .sidebar-item-control,
            .body-sidebar .section-item > .standard-sidebar-item .drop-icon {
                min-width: 28px !important;
                min-height: 28px !important;
                cursor: pointer !important;
            }
            .body-sidebar .sidebar-child-item .sidebar-item-icon {
                display: none !important;
            }
            .body-sidebar .sidebar-child-item .standard-sidebar-item .item-anchor {
                padding-left: 24px !important;
                font-size: 13px !important;
                font-weight: 400 !important;
            }
            .body-sidebar .standard-sidebar-item.ashan-workbench-item .sidebar-item-label {
                font-weight: 700 !important;
                color: var(--text-color) !important;
            }
        `;
        document.head.appendChild(style);
    }

    function markWorkbenchItems() {
        const sidebar = document.querySelector(".body-sidebar");
        if (!sidebar) return;

        sidebar.querySelectorAll(".sidebar-child-item .standard-sidebar-item").forEach((item) => {
            const text = (item.textContent || "").trim();
            const important = (
                text.includes("工作台") ||
                text.includes("总览") ||
                text.includes("资料库") ||
                text.includes("台账明细台")
            );
            item.classList.toggle("ashan-workbench-item", important);
        });
    }

    function applyOilOperatorView() {
        if (!isPureOilOperator()) return;
        const sidebar = document.querySelector(".body-sidebar");
        if (!sidebar) return;

        sidebar.querySelectorAll("a").forEach((anchor) => {
            const text = (anchor.textContent || "").trim();
            const href = (anchor.getAttribute("href") || "").toLowerCase();
            if (text.includes("我的业务") || href.includes("workspaces/home")) {
                const row = anchor.closest(".standard-sidebar-item, .sidebar-item-container");
                if (row) row.style.display = "none";
            }
        });

        sidebar.querySelectorAll(".section-item").forEach((sectionEl) => {
            const title = (
                sectionEl.getAttribute("item-name") ||
                sectionEl.getAttribute("title") ||
                sectionEl.querySelector(".sidebar-item-label")?.textContent ||
                ""
            ).trim();

            const keep = title.includes("车辆") || title.includes("油卡");
            if (!keep) {
                sectionEl.style.display = "none";
                const children = sectionEl.querySelectorAll(".sidebar-child-item");
                children.forEach((child) => child.style.display = "none");
            }
        });

        sidebar.querySelectorAll(".sidebar-child-item .standard-sidebar-item").forEach((row) => {
            const anchor = row.querySelector("a");
            const text = (row.textContent || "").trim();
            const href = (anchor?.getAttribute("href") || "").toLowerCase();
            const keep = href.includes("oil-card-ledger") || text.includes("油卡综合台账");
            if (!keep) row.style.display = "none";
        });
    }

    function bindSectionNavigation() {
        if (!window.jQuery) return;
        const $doc = jQuery(document);
        const selector = ".body-sidebar .section-item > .standard-sidebar-item .sidebar-item-label";

        $doc.off("click.ashanSidebarV2", selector);
        $doc.on("click.ashanSidebarV2", selector, function () {
            const $section = jQuery(this).closest(".section-item");
            const title = (
                $section.attr("item-name") ||
                $section.attr("title") ||
                jQuery(this).text() ||
                ""
            ).trim();
            const target = SECTION_ROUTES[title];
            if (!target || !window.frappe || !frappe.set_route) return;

            // Do not cancel Frappe's native click. Let the native Section Break
            // open/close first, then navigate to the related dashboard.
            window.setTimeout(() => frappe.set_route(...target), 0);
        });
    }

    let refreshTimer = null;
    function refreshSidebarEnhancements() {
        window.clearTimeout(refreshTimer);
        refreshTimer = window.setTimeout(() => {
            injectStyles();
            patchSidebarResolver();
            bindSectionNavigation();
            markWorkbenchItems();
            applyOilOperatorView();
        }, 30);
    }

    function observeSidebar() {
        if (!document.body || window.__ashanSidebarV2Observer) return;
        const observer = new MutationObserver(refreshSidebarEnhancements);
        observer.observe(document.body, { childList: true, subtree: true });
        window.__ashanSidebarV2Observer = observer;
    }

    function init() {
        if (!window.frappe) {
            window.setTimeout(init, 100);
            return;
        }
        refreshSidebarEnhancements();
        handleRootRoute();
        observeSidebar();

        if (frappe.router && frappe.router.on && !window.__ashanSidebarV2RouteBound) {
            frappe.router.on("change", () => {
                handleRootRoute();
                refreshSidebarEnhancements();
            });
            window.__ashanSidebarV2RouteBound = true;
        }
    }

    init();
    if (window.jQuery) {
        jQuery(document).ready(init);
        jQuery(document).on("app_ready sidebar_setup", init);
    }
})();

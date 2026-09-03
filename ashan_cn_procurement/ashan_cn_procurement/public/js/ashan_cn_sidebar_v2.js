/* ==========================================================================
   ERPNext 16 业务扩展 - Sidebar V2
   Goals:
   1) Keep the business sidebar persistent on Buying/Stock/Accounts/Selling docs.
   2) Keep one smooth, deterministic accordion state for the two-level menu.
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

        // 严格检查浏览器真实地址：只有直接访问根路径时才执行首页重定向
        const pathname = (window.location.pathname || "").toLowerCase().replace(/\/+$/, "");
        const hash = (window.location.hash || "").toLowerCase();

        const isTrueRootUrl = (
            pathname === "" ||
            pathname === "/" ||
            pathname === "/desk" ||
            pathname === "/app"
        ) && (hash === "" || hash === "#" || hash === "#desk" || hash === "#app");

        if (!isTrueRootUrl) {
            return;
        }

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

    function patchNativeSidebarMethods() {
        if (!window.frappe || !frappe.ui || !frappe.ui.Sidebar) return false;
        const Sidebar = frappe.ui.Sidebar;
        if (Sidebar._ashan_native_methods_patched) return true;

        // 接管原生 set_active_workspace_item 与 expand_parent_section，杜绝原生 naive 匹配导致的跨企业跳动
        Sidebar.prototype.set_active_workspace_item = function () {
            const sidebar = document.querySelector(".body-sidebar");
            if (sidebar) {
                scheduleAccordionHydration(sidebar);
            }
        };

        Sidebar.prototype.expand_parent_section = function () {
            const sidebar = document.querySelector(".body-sidebar");
            if (sidebar) {
                scheduleAccordionHydration(sidebar);
            }
        };

        Sidebar._ashan_native_methods_patched = true;
        return true;
    }

    let lastFetchedKpis = null;
    let kpiFetchPending = false;

    async function fetchSidebarKpis(force = false) {
        if (!window.frappe || !frappe.call) return null;
        if (window.frappe.session && window.frappe.session.user === "Guest") return null;
        if (lastFetchedKpis && !force) return lastFetchedKpis;
        if (kpiFetchPending) return lastFetchedKpis;
        kpiFetchPending = true;
        try {
            const r = await frappe.call({
                method: "ashan_cn_procurement.services.procurement_picker_service.get_sidebar_notification_kpis",
                args: {},
                freeze: false,
            });
            kpiFetchPending = false;
            if (r && r.message) {
                lastFetchedKpis = r.message;
                return r.message;
            }
        } catch (e) {
            kpiFetchPending = false;
        }
        return lastFetchedKpis;
    }

    function renderSidebarBadges(kpis) {
        if (!kpis) return;
        const sidebar = document.querySelector(".body-sidebar");
        if (!sidebar) return;

        sidebar.querySelectorAll(".sidebar-child-item a.item-anchor, .sidebar-child-item a[href]").forEach((anchor) => {
            const href = (anchor.getAttribute("href") || "").toLowerCase();
            const text = (anchor.textContent || "").trim();

            let count = 0;
            let tooltip = "";

            if (href.includes("material-receipt-workbench") || text.includes("收货入库")) {
                count = Number(kpis["material-receipt-workbench"]) || 0;
                tooltip = `${count} 笔采购订单等待实际入库`;
            } else if (href.includes("procurement-execution-workbench") || text.includes("采购执行")) {
                count = Number(kpis["procurement-execution-workbench"]) || 0;
                tooltip = `${count} 笔采购申请等待下单`;
            } else if (href.includes("material-request-workbench") || text.includes("物料申请")) {
                count = Number(kpis["material-request-workbench"]) || 0;
                tooltip = `${count} 笔物料申请草稿待提交`;
            } else if (href.includes("stock-issue-workbench") || text.includes("材料出库")) {
                count = Number(kpis["stock-issue-workbench"]) || 0;
                tooltip = `${count} 笔材料出库草稿待提交`;
            }

            let badge = anchor.querySelector(".ashan-sidebar-count-badge");
            if (count > 0) {
                if (!badge) {
                    badge = document.createElement("span");
                    badge.className = "ashan-sidebar-count-badge";
                    anchor.appendChild(badge);
                }
                badge.textContent = count > 99 ? "99+" : String(count);
                badge.setAttribute("title", tooltip);
            } else if (badge) {
                badge.remove();
            }
        });
    }

    async function updateSidebarBadges(force = false) {
        const kpis = await fetchSidebarKpis(force);
        if (kpis) {
            renderSidebarBadges(kpis);
        }
    }

    // Expose global hook for workbench refresh
    window.AshanUI = window.AshanUI || {};
    window.AshanUI.refreshSidebarBadges = () => updateSidebarBadges(true);

    function markWorkbenchItems() {
        const sidebar = document.querySelector(".body-sidebar");
        if (!sidebar) return;

        sidebar.querySelectorAll(".sidebar-child-item .standard-sidebar-item").forEach((item) => {
            const text = (item.textContent || "").trim();
            const important = (
                text.includes("工作台") ||
                text.includes("总览") ||
                text.includes("资料库") ||
                text.includes("台账明细台") ||
                text.includes("全景中枢") ||
                text.includes("核定中枢")
            );
            item.classList.toggle("ashan-workbench-item", important);
        });

        updateSidebarBadges(false);
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

    function getAccordionStorageKey() {
        const user = window.frappe?.session?.user || "anonymous";
        return `ashan.sidebar.v3.open-section.${user}`;
    }

    function getSectionId(section) {
        return (
            section.dataset.id ||
            section.getAttribute("item-name") ||
            section.getAttribute("title") ||
            ""
        ).trim();
    }

    function getSidebarSections(sidebar) {
        return Array.from(sidebar.querySelectorAll(".sidebar-items > .section-item"));
    }

    function setAccordionState(sidebar, openId, persist = true) {
        getSidebarSections(sidebar).forEach((section) => {
            const isOpen = Boolean(openId) && getSectionId(section) === openId;
            if (section.classList.contains("ashan-sidebar-section-expanded") !== isOpen) {
                section.classList.toggle("ashan-sidebar-section-expanded", isOpen);
            }
            const trigger = section.querySelector(
                ":scope > .standard-sidebar-item .item-anchor"
            );
            if (trigger) {
                trigger.setAttribute("role", "button");
                trigger.setAttribute("tabindex", "0");
                trigger.setAttribute("aria-expanded", String(isOpen));
            }

            // 同步 Frappe 原生嵌套容器的 class 与状态，彻底避免与原生 Desk 冲突
            const childContainer = section.querySelector(":scope > .sidebar-child-item");
            if (childContainer) {
                if (isOpen) {
                    childContainer.classList.remove("hidden");
                } else {
                    childContainer.classList.add("hidden");
                }
            }

            const dropIcon = section.querySelector(".drop-icon");
            if (dropIcon) {
                dropIcon.setAttribute("data-state", isOpen ? "opened" : "closed");
                const iconUse = dropIcon.querySelector("use");
                if (iconUse) {
                    iconUse.setAttribute("href", isOpen ? "#icon-chevron-down" : "#icon-chevron-right");
                }
            }

            if (window.frappe?.app?.sidebar?.items) {
                const sId = getSectionId(section);
                const nativeItem = window.frappe.app.sidebar.items.find(
                    (it) => it.item && (it.item.label === sId || it.item.title === sId)
                );
                if (nativeItem) {
                    nativeItem.collapsed = !isOpen;
                }
            }
        });

        if (persist) {
            try {
                window.sessionStorage.setItem(getAccordionStorageKey(), openId || "");
            } catch (error) {
                // Storage can be unavailable in privacy-restricted browser sessions.
            }
        }
    }

    function getRouteTokens() {
        const route = window.frappe?.get_route?.() || [];
        if (!route || !route.length) return [];
        const routeTokens = [];
        const joined = route.join("/").toLowerCase();
        routeTokens.push(joined);

        route.forEach((segment) => {
            if (typeof segment === "string" && segment.trim()) {
                const s = segment.trim().toLowerCase();
                routeTokens.push(s);
                routeTokens.push(s.replace(/[\s_]+/g, "-"));
            }
        });
        return routeTokens;
    }

    function sectionMatchesRoute(section, routeTokens) {
        if (!section || !routeTokens || !routeTokens.length) return false;
        return Array.from(
            section.querySelectorAll(":scope > .sidebar-child-item a[href]")
        ).some((anchor) => {
            const rawHref = (anchor.getAttribute("href") || "").toLowerCase();
            const cleanHref = rawHref.replace(/^\/desk\//, "").replace(/^\/app\//, "").replace(/^\//, "");
            return routeTokens.some((token) => token && (cleanHref === token || cleanHref.includes(token) || token.includes(cleanHref)));
        });
    }

    function detectCompanyContext() {
        // 1. URL 查询参数优先：例如 ?company=天津吉众科技有限公司
        try {
            const urlParams = new URLSearchParams(window.location.search);
            const compInUrl = urlParams.get("company");
            if (compInUrl) {
                if (compInUrl.includes("吉众")) return "吉众";
                if (compInUrl.includes("祺富")) return "祺富";
            }
        } catch (e) {}

        // 2. Frappe route_options 参数：例如 frappe.route_options = { company: '天津吉众科技有限公司' }
        try {
            const roComp = window.frappe?.route_options?.company;
            if (roComp && typeof roComp === "string") {
                if (roComp.includes("吉众")) return "吉众";
                if (roComp.includes("祺富")) return "祺富";
            }
        } catch (e) {}

        // 3. 当前路由/页面标识：例如 jizhong-hr-salary-workbench 或 qifu-hr-salary-workbench
        const route = window.frappe?.get_route?.() || [];
        const joined = route.join("/").toLowerCase();
        if (joined.includes("jizhong") || joined.includes("吉众")) return "吉众";
        if (joined.includes("qifu") || joined.includes("祺富")) return "祺富";

        // 4. 当前列表筛选器 (cur_list)：
        try {
            if (window.cur_list && window.cur_list.filter_area) {
                const filters = window.cur_list.filter_area.get() || [];
                for (const f of filters) {
                    if (f[1] === "company" && typeof f[3] === "string") {
                        if (f[3].includes("吉众")) return "吉众";
                        if (f[3].includes("祺富")) return "祺富";
                    }
                }
            }
        } catch (e) {}

        // 5. 当前表单 (cur_frm)：
        try {
            if (window.cur_frm && window.cur_frm.doc && window.cur_frm.doc.company) {
                const docComp = window.cur_frm.doc.company;
                if (docComp.includes("吉众")) return "吉众";
                if (docComp.includes("祺富")) return "祺富";
            }
        } catch (e) {}

        // 6. 用户最近显式选定或点击的分组缓存 (sessionStorage)
        try {
            const cachedCompany = window.sessionStorage.getItem("ashan.sidebar.v3.active_company_context") || "";
            if (cachedCompany.includes("吉众")) return "吉众";
            if (cachedCompany.includes("祺富")) return "祺富";
            const lastClicked = window.sessionStorage.getItem("ashan.sidebar.v3.last_clicked_section") || "";
            if (lastClicked.includes("吉众")) return "吉众";
            if (lastClicked.includes("祺富")) return "祺富";
        } catch (e) {}

        return "";
    }

    function getActiveSectionId(sidebar) {
        const sections = getSidebarSections(sidebar);
        if (!sections.length) return "";

        const routeTokens = getRouteTokens();
        if (!routeTokens.length) return "";

        const companyContext = detectCompanyContext();

        // 1. 如果检测到明确的企业上下文（吉众 或 祺富），优先精准命中该企业的专属分组
        if (companyContext === "吉众") {
            const jzSection = sections.find((s) => getSectionId(s).includes("吉众"));
            if (jzSection && sectionMatchesRoute(jzSection, routeTokens)) {
                return getSectionId(jzSection);
            }
        } else if (companyContext === "祺富") {
            const qfSection = sections.find((s) => getSectionId(s).includes("祺富"));
            if (qfSection && sectionMatchesRoute(qfSection, routeTokens)) {
                return getSectionId(qfSection);
            }
        }

        // 2. 坚守用户最近显式点击的分组（只要该分组能够匹配当前路由）
        let savedId = "";
        try {
            savedId = window.sessionStorage.getItem("ashan.sidebar.v3.last_clicked_section") ||
                      window.sessionStorage.getItem(getAccordionStorageKey()) || "";
        } catch (e) {}

        if (savedId) {
            const savedSection = sections.find((s) => getSectionId(s) === savedId);
            if (savedSection && sectionMatchesRoute(savedSection, routeTokens)) {
                return savedId;
            }
        }

        // 3. 检查原生选中的元素所在分组（必须确实包含该路由）
        const activeSection = sections.find((section) => section.querySelector(
            ".sidebar-child-item.active, .sidebar-child-item.selected, .sidebar-child-item.active-sidebar, " +
            ".sidebar-child-item .active, .sidebar-child-item .selected, .sidebar-child-item .active-sidebar"
        ));
        if (activeSection && sectionMatchesRoute(activeSection, routeTokens)) {
            if (companyContext === "吉众" && getSectionId(activeSection).includes("祺富")) {
                // 严禁吉众上下文跳去祺富
            } else if (companyContext === "祺富" && getSectionId(activeSection).includes("吉众")) {
                // 严禁祺富上下文跳去吉众
            } else {
                return getSectionId(activeSection);
            }
        }

        // 4. 通用兜底：从所有分组中找到包含该路由的分组（严格遵守企业物理隔离，绝不跳去对手企业）
        const routeSection = sections.find((section) => {
            const sId = getSectionId(section);
            if (companyContext === "吉众" && sId.includes("祺富")) return false;
            if (companyContext === "祺富" && sId.includes("吉众")) return false;
            return sectionMatchesRoute(section, routeTokens);
        });
        return routeSection ? getSectionId(routeSection) : "";
    }

    function syncAccordionState() {
        const sidebar = document.querySelector(".body-sidebar");
        if (!sidebar) return "";

        const sections = getSidebarSections(sidebar);
        if (!sections.length) return "";

        let savedId = "";
        try {
            savedId = window.sessionStorage.getItem("ashan.sidebar.v3.last_clicked_section") ||
                      window.sessionStorage.getItem(getAccordionStorageKey()) || "";
        } catch (error) {
            savedId = "";
        }

        const activeId = getActiveSectionId(sidebar);
        const savedIdExists = sections.some((section) => getSectionId(section) === savedId);
        // 当前路由的归属优先于陈旧历史记忆，但如果当前记忆分组有效命中，则由 getActiveSectionId 优先保证
        const openId = activeId || (savedIdExists ? savedId : "");
        setAccordionState(sidebar, openId, false);
        return openId;
    }

    function highlightActiveSidebarItem(sidebar, targetSectionId) {
        if (!sidebar) return;
        const routeTokens = getRouteTokens();
        if (!routeTokens.length) return;
        const joined = routeTokens[0] || "";
        const route = window.frappe?.get_route?.() || [];
        const primary = String(route[0] || "").toLowerCase().replace(/[\s_]+/g, "-");

        // 1. 先清除整个侧边栏中所有子项的 active / selected / active-sidebar 状态，防止多企业或跨分组产生多重幽灵高亮
        sidebar.querySelectorAll(".sidebar-child-item, .standard-sidebar-item").forEach((el) => {
            el.classList.remove("active", "selected", "active-sidebar");
        });

        // 2. 如果指定了 targetSectionId，则仅在其限定的作用域内进行高亮匹配
        let scopeEl = sidebar;
        if (targetSectionId) {
            const sections = getSidebarSections(sidebar);
            const targetSection = sections.find((s) => getSectionId(s) === targetSectionId);
            if (targetSection) {
                scopeEl = targetSection;
            }
        }

        scopeEl.querySelectorAll(".sidebar-child-item").forEach((child) => {
            const anchor = child.querySelector("a[href]");
            if (!anchor) return;
            const rawHref = (anchor.getAttribute("href") || "").toLowerCase();
            const cleanHref = rawHref.replace(/^\/desk\//, "").replace(/^\/app\//, "").replace(/^\//, "");
            const isMatch = cleanHref === joined || cleanHref === primary || (joined.startsWith(cleanHref) && cleanHref.length > 3);
            if (isMatch) {
                child.classList.add("active", "selected", "active-sidebar");
                child.querySelector(".standard-sidebar-item")?.classList.add("active", "selected", "active-sidebar");
            }
        });
    }

    let pendingHydrationFrame = null;
    function hydrateAccordionState(sidebar) {
        if (!sidebar || sidebar !== document.querySelector(".body-sidebar")) return;
        sidebar.dataset.ashanSidebarHydrating = "true";
        const openId = syncAccordionState();
        highlightActiveSidebarItem(sidebar, openId);
        window.requestAnimationFrame(() => {
            if (sidebar === document.querySelector(".body-sidebar")) {
                delete sidebar.dataset.ashanSidebarHydrating;
            }
        });
    }

    function scheduleAccordionHydration(sidebar) {
        if (!sidebar) return;
        if (pendingHydrationFrame) {
            window.cancelAnimationFrame(pendingHydrationFrame);
        }
        pendingHydrationFrame = window.requestAnimationFrame(() => {
            pendingHydrationFrame = null;
            hydrateAccordionState(sidebar);
            updateSidebarBadges(false);
        });
    }

    function bindAccordionInteractions() {
        if (window.__ashanSidebarV2AccordionBound) return;

        const toggleSection = (target) => {
            if (target.closest(".sidebar-item-edit-controls")) return false;

            const trigger = target.closest(
                ".body-sidebar .section-item > .standard-sidebar-item"
            );
            if (!trigger) return false;

            const sidebar = trigger.closest(".body-sidebar");
            const section = trigger.closest(".section-item");
            if (
                !sidebar ||
                !section ||
                !section.parentElement?.classList.contains("sidebar-items")
            ) return false;

            const sectionId = getSectionId(section);
            const willOpen = !section.classList.contains(
                "ashan-sidebar-section-expanded"
            );
            setAccordionState(sidebar, willOpen ? sectionId : "");
            if (willOpen && sectionId) {
                try {
                    window.sessionStorage.setItem("ashan.sidebar.v3.last_clicked_section", sectionId);
                    if (sectionId.includes("吉众")) {
                        window.sessionStorage.setItem("ashan.sidebar.v3.active_company_context", "吉众");
                    } else if (sectionId.includes("祺富")) {
                        window.sessionStorage.setItem("ashan.sidebar.v3.active_company_context", "祺富");
                    }
                } catch (e) {}
            }
            return true;
        };

        document.addEventListener("click", (event) => {
            if (toggleSection(event.target)) {
                // Section breaks are toggles, not navigation targets. Capturing the
                // event prevents native/legacy handlers from applying a second,
                // global toggle to every section.
                event.preventDefault();
                event.stopImmediatePropagation();
                return;
            }

            const childAnchor = event.target.closest(
                ".body-sidebar .section-item > .sidebar-child-item .item-anchor"
            );
            if (!childAnchor) return;
            const sidebar = childAnchor.closest(".body-sidebar");
            const section = childAnchor.closest(".section-item");
            const sectionId = section ? getSectionId(section) : "";
            if (sidebar && sectionId) {
                // 二级跳转立即记住当前分组；不在这里折叠或重建任何其它分组。
                setAccordionState(sidebar, sectionId, true);
                try {
                    window.sessionStorage.setItem("ashan.sidebar.v3.last_clicked_section", sectionId);
                    if (sectionId.includes("吉众")) {
                        window.sessionStorage.setItem("ashan.sidebar.v3.active_company_context", "吉众");
                    } else if (sectionId.includes("祺富")) {
                        window.sessionStorage.setItem("ashan.sidebar.v3.active_company_context", "祺富");
                    }
                } catch (e) {}

                // 核心隔离：若点击吉众或祺富的考勤/核定/档案/社保，自动注入目标公司上下文
                if (sectionId.includes("吉众")) {
                    window.frappe = window.frappe || {};
                    window.frappe.route_options = window.frappe.route_options || {};
                    window.frappe.route_options["company"] = "天津吉众科技有限公司";
                } else if (sectionId.includes("祺富")) {
                    window.frappe = window.frappe || {};
                    window.frappe.route_options = window.frappe.route_options || {};
                    window.frappe.route_options["company"] = "天津市祺富汽车配件有限公司";
                }
            }
        }, true);

        document.addEventListener("keydown", (event) => {
            if (event.key !== "Enter" && event.key !== " ") return;
            if (!toggleSection(event.target)) return;
            event.preventDefault();
            event.stopImmediatePropagation();
        }, true);

        window.__ashanSidebarV2AccordionBound = true;
    }

    let refreshFrame = null;
    let refreshNeedsHydration = false;
    function refreshSidebarEnhancements(restoreState = false) {
        refreshNeedsHydration = refreshNeedsHydration || restoreState;
        if (refreshFrame) return;
        refreshFrame = window.requestAnimationFrame(() => {
            const shouldRestoreState = refreshNeedsHydration;
            refreshFrame = null;
            refreshNeedsHydration = false;
            patchSidebarResolver();
            patchNativeSidebarMethods();
            bindAccordionInteractions();
            markWorkbenchItems();
            applyOilOperatorView();
            observeSidebar();
            if (shouldRestoreState) {
                scheduleAccordionHydration(document.querySelector(".body-sidebar"));
            }
        });
    }

    let sidebarItemsObserver = null;
    let observedSidebarItems = null;
    function observeSidebar() {
        const sidebar = document.querySelector(".body-sidebar");
        const items = sidebar?.querySelector(".sidebar-items");
        if (!items) {
            sidebarItemsObserver?.disconnect();
            sidebarItemsObserver = null;
            observedSidebarItems = null;
            return;
        }
        if (observedSidebarItems === items) return;

        sidebarItemsObserver?.disconnect();
        sidebarItemsObserver = new MutationObserver(() => {
            // 只响应一级分组容器被 Frappe 重建，忽略二级项激活、内容加载等内部变动。
            scheduleAccordionHydration(sidebar);
        });
        sidebarItemsObserver.observe(items, { childList: true });
        observedSidebarItems = items;
        scheduleAccordionHydration(sidebar);
    }

    function init() {
        if (!window.frappe) {
            window.setTimeout(init, 100);
            return;
        }
        patchSidebarResolver();
        patchNativeSidebarMethods();
        refreshSidebarEnhancements(true);
        handleRootRoute();
        observeSidebar();

        if (frappe.router && frappe.router.on && !window.__ashanSidebarV2RouteBound) {
            frappe.router.on("change", () => {
                handleRootRoute();
                refreshSidebarEnhancements(true);
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

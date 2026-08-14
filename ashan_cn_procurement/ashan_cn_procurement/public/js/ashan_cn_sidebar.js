/* ==========================================================================
   ERPNext 16 业务扩展 - 精准层级解耦架构 (Strict Hierarchy Isolation)
   1. 一级菜单小箭头：仅折叠/展开当前一级菜单
   2. 一级菜单文字区：折叠/展开当前一级菜单 + 联动分类 Dashboard
   3. 二级菜单单据项：绝对不触发折叠/展开，仅纯粹跳转对应单据页面
   ========================================================================== */

(function() {
    // 0. 路由全局重定向规则
    if (window.frappe) {
        frappe.re_route = frappe.re_route || {};
        frappe.re_route[""] = "desk/my-business";
        frappe.re_route["desk"] = "desk/my-business";
        frappe.re_route["app"] = "desk/my-business";
        frappe.re_route["Workspaces"] = "desk/my-business";
        frappe.re_route["workspaces"] = "desk/my-business";
    }

    // 1. 一级标题 → 对应 Workspace 映射
    const SECTION_WORKSPACE_MAP = {
        "仓库与库存": "stock-and-inventory",
        "库存": "stock-and-inventory",
        "采购协同": "procurement-management",
        "采购": "procurement-management",
        "车辆燃油": "vehicle-fuel-hub",
        "车油能耗中心": "vehicle-fuel-hub",
        "燃油管理": "vehicle-fuel-hub",
        "公司合规": "company-compliance-center",
        "企业合规中心": "company-compliance-center",
        "公司治理": "company-compliance-center",
        "财务与报销": "accounting-and-finance",
        "财务": "accounting-and-finance",
        "我的业务 (总主页)": "my-business",
        "我的业务 (总控主页)": "my-business",
        "我的业务 (总看板)": "my-business",
        "我的业务": "my-business"
    };

    const ALL_WS_KEYS = [
        "my business", "my-business",
        "stock and inventory", "stock-and-inventory",
        "procurement management", "procurement-management",
        "vehicle fuel hub", "vehicle-fuel-hub",
        "company compliance center", "company-compliance-center",
        "accounting and finance", "accounting-and-finance",
        "ashan cn procurement", "ashan_cn_procurement",
        "业务扩展"
    ];

    // 2. 深度重写 Frappe 原生 TypeSectionBreak 原型方法
    function patch_native_section_break() {
        if (!window.frappe || !frappe.ui || !frappe.ui.sidebar_item || !frappe.ui.sidebar_item.TypeSectionBreak) {
            return false;
        }

        const TypeSectionBreak = frappe.ui.sidebar_item.TypeSectionBreak;
        if (TypeSectionBreak._ashan_strict_patched) return true;

        // 丝滑动画切换 toggle()
        TypeSectionBreak.prototype.toggle = function(animate = true) {
            const $nested = $(this.$nested_items);
            if (!$nested.length) return;

            $nested.removeClass("hidden");

            if (this.collapsed) {
                if (this.$drop_icon) {
                    this.$drop_icon.attr("data-state", "closed").find("use").attr("href", "#icon-chevron-right");
                }
                $(this.wrapper).attr("data-state", "closed");
                if (animate) {
                    $nested.stop(true, true).slideUp(180);
                } else {
                    $nested.hide();
                }
            } else {
                if (this.$drop_icon) {
                    this.$drop_icon.attr("data-state", "opened").find("use").attr("href", "#icon-chevron-down");
                }
                $(this.wrapper).attr("data-state", "opened");
                if (animate) {
                    $nested.stop(true, true).slideDown(180);
                } else {
                    $nested.show();
                }
            }
        };

        // 状态持久化
        TypeSectionBreak.prototype.save_section_break_state = function() {
            try {
                let state = JSON.parse(localStorage.getItem("section-breaks-state") || "{}");
                const title = (this.wrapper.attr("item-name") || this.wrapper.attr("title") || "").trim();
                if (title) {
                    ALL_WS_KEYS.forEach(k => {
                        if (!state[k]) state[k] = {};
                        state[k][title] = this.collapsed;
                    });
                    this.section_breaks_state = state;
                    localStorage.setItem("section-breaks-state", JSON.stringify(state));
                }
            } catch(e) {}
        };

        // 严格层级解耦：只给一级标题的元素绑定事件，绝对不污染二级子菜单
        TypeSectionBreak.prototype.setup_event_listner = function() {
            const me = this;
            // 仅获取当前 SectionBreak 自身的第一层 .standard-sidebar-item（排除子菜单）
            const $l1_standard_item = this.wrapper.children(".standard-sidebar-item");
            if (!$l1_standard_item.length) return;

            $l1_standard_item.off("click");

            // [1] 一级右侧小箭头按钮 -> 仅执行手风琴折叠/展开
            $l1_standard_item.find(".sidebar-item-control, .drop-icon").off("click").on("click", function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (e.stopImmediatePropagation) e.stopImmediatePropagation();
                me.collapsed = !me.collapsed;
                me.toggle(true);
                me.save_section_break_state();
            });

            // [2] 一级左侧文字与图标 -> 仅在一级标题点击时触发折叠/展开 + 联动看板
            $l1_standard_item.find(".sidebar-item-label, .sidebar-item-icon, .item-anchor").off("click").on("click", function(e) {
                if ($(e.target).closest(".sidebar-item-control, .drop-icon").length) return;

                e.preventDefault();
                e.stopPropagation();

                // 丝滑展开/折叠切换当前一级菜单
                me.collapsed = !me.collapsed;
                me.toggle(true);
                me.save_section_break_state();

                // 联动跳转至对应分类 Dashboard
                const title = (me.wrapper.attr("item-name") || me.wrapper.attr("title") || "").trim();
                const targetWs = SECTION_WORKSPACE_MAP[title];
                if (targetWs) {
                    try {
                        const currentRoute = (frappe.router && frappe.router.current_route) ? (frappe.get_route_str() || "") : "";
                        if (!currentRoute.includes(targetWs)) {
                            frappe.set_route("desk", targetWs);
                        }
                    } catch(err) {}
                }
            });
        };

        TypeSectionBreak._ashan_strict_patched = true;
        return true;
    }

    // 3. 注入样式
    function inject_styles() {
        if ($("#ashan-strict-style").length) return;
        const styleHtml = `
        <style id="ashan-strict-style">
            /* 一级分类标题加粗与平滑过渡 */
            .body-sidebar .section-item > .standard-sidebar-item .item-anchor {
                cursor: pointer !important;
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                border-radius: var(--border-radius, 6px);
                transition: background-color 0.15s ease;
                padding: 4px 8px !important;
                user-select: none;
            }
            .body-sidebar .section-item > .standard-sidebar-item .item-anchor:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
            .body-sidebar .section-item > .standard-sidebar-item .sidebar-item-label {
                font-weight: 700 !important;
                font-size: 13.5px !important;
                color: var(--text-color, #1f272e) !important;
                flex: 1 !important;
                cursor: pointer !important;
                transition: color 0.15s ease;
            }
            .body-sidebar .section-item > .standard-sidebar-item .sidebar-item-label:hover {
                color: var(--primary-color, #2f54eb) !important;
            }
            /* 右侧独立小箭头 */
            .body-sidebar .section-item > .standard-sidebar-item .sidebar-item-control {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                margin-left: auto !important;
                z-index: 10;
            }
            .body-sidebar .section-item > .standard-sidebar-item .sidebar-item-control .drop-icon {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: 28px !important;
                height: 28px !important;
                border-radius: 4px !important;
                cursor: pointer !important;
                transition: background-color 0.15s ease, transform 0.15s ease;
                pointer-events: auto !important;
            }
            .body-sidebar .section-item > .standard-sidebar-item .sidebar-item-control .drop-icon:hover {
                background-color: rgba(0, 0, 0, 0.12) !important;
            }
            /* 二级菜单严格去图标并缩进，且拥有独立的普通悬停样式，绝不与一级混淆 */
            .body-sidebar .sidebar-child-item .sidebar-item-icon {
                display: none !important;
            }
            .body-sidebar .sidebar-child-item .standard-sidebar-item .item-anchor {
                padding-left: 24px !important;
                font-size: 13px !important;
                font-weight: 400 !important;
                cursor: pointer !important;
            }
        </style>
        `;
        $("head").append(styleHtml);
    }

    // 4. 初始化挂载
    function init() {
        inject_styles();
        patch_native_section_break();

        $(document).on("sidebar_setup", function() {
            inject_styles();
            patch_native_section_break();
        });
    }

    $(document).on("app_ready", init);
    $(document).ready(function() {
        if (window.frappe) init();
    });
})();

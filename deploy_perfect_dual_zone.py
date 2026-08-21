import os
import paramiko

def load_env_file(env_path='.env'):
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env_file()
HOST = os.getenv('UNRAID_SSH_HOST', '192.168.8.11')
PORT = int(os.getenv('UNRAID_SSH_PORT', '22'))
USER_SSH = os.getenv('UNRAID_SSH_USER', 'root')
PASSWORD = os.getenv('UNRAID_SSH_PASSWORD', '')

PERFECT_JS = """/* ==========================================================================
   ERPNext 16 业务扩展 - 侧边栏“职责分离”双区交互模型 (Dual-Zone Action Model)
   - 文字/图标区域：直达对应业务分类看板（Workspace Dashboard），并自动保证展开
   - 箭头按钮独立区域：纯粹展开/收起手风琴折叠树，绝不干扰页面跳转
   ========================================================================== */

(function() {
    // 0. 路由全局重定向规则（根路径直达 my-business 看板）
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

    // 2. 自定义 Sidebar 固定 key（localStorage 隔离）
    const ASHAN_SIDEBAR_KEY = "ashan-cn-sidebar-state";

    function get_sidebar_state() {
        try {
            return JSON.parse(localStorage.getItem(ASHAN_SIDEBAR_KEY) || "{}");
        } catch(e) {
            return {};
        }
    }

    function set_section_state(section_title, collapsed) {
        let state = get_sidebar_state();
        state[section_title] = collapsed;
        try {
            localStorage.setItem(ASHAN_SIDEBAR_KEY, JSON.stringify(state));
        } catch(e) {}
    }

    function get_section_state(section_title) {
        let state = get_sidebar_state();
        return state.hasOwnProperty(section_title) ? state[section_title] : false;
    }

    // 3. 展开/折叠指定 section DOM 动作
    function toggle_section($container, force_open = null) {
        const section_title = ($container.attr("item-name") || $container.attr("title") || "").trim();
        if (!section_title) return;

        const $children = $container.find(".sidebar-child-item");
        const $dropIcon = $container.find(".drop-icon use, .btn-reset use");
        const current_is_closed = $container.attr("data-state") === "closed" || $children.is(":hidden");

        let target_open = (force_open !== null) ? force_open : current_is_closed;

        if (target_open) {
            $children.attr("data-state", "opened").show();
            $container.attr("data-state", "opened");
            $dropIcon.attr("href", "#icon-chevron-up");
            set_section_state(section_title, false);
        } else {
            $children.attr("data-state", "closed").hide();
            $container.attr("data-state", "closed");
            $dropIcon.attr("href", "#icon-chevron-down");
            set_section_state(section_title, true);
        }
    }

    // 4. 恢复侧边栏各 section 的折叠/展开状态
    function restore_sidebar_states() {
        try {
            const $sections = $(".body-sidebar .section-item");
            if (!$sections.length) return;

            $sections.each(function() {
                const $container = $(this).closest(".sidebar-item-container");
                const section_title = (
                    $container.attr("item-name") ||
                    $container.attr("title") ||
                    ""
                ).trim();

                if (!section_title) return;

                const should_collapse = get_section_state(section_title);
                const $children = $container.find(".sidebar-child-item");
                const $dropIcon = $container.find(".drop-icon use, .btn-reset use");

                if (should_collapse) {
                    $children.attr("data-state", "closed").hide();
                    $container.attr("data-state", "closed");
                    $dropIcon.attr("href", "#icon-chevron-down");
                } else {
                    $children.attr("data-state", "opened").show();
                    $container.attr("data-state", "opened");
                    $dropIcon.attr("href", "#icon-chevron-up");
                }
            });
        } catch(e) {
            console.error("restore_sidebar_states error:", e);
        }
    }

    // 5. 绑定“职责分离”双区交互事件
    function setup_dual_zone_handlers() {
        // [区域 A]：点击右侧箭头按钮 -> 纯粹折叠/展开手风琴，绝不跳转页面
        $(document).off("click.ashan_toggle").on(
            "click.ashan_toggle",
            ".body-sidebar .section-item .sidebar-item-control, .body-sidebar .section-item .drop-icon, .body-sidebar .section-item .drop-icon *",
            function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (e.stopImmediatePropagation) e.stopImmediatePropagation();
                const $container = $(this).closest(".sidebar-item-container");
                toggle_section($container);
            }
        );

        // [区域 B]：点击左侧文字与图标 -> 直达对应分类看板 (Workspace Dashboard) 并确保菜单展开
        $(document).off("click.ashan_nav").on(
            "click.ashan_nav",
            ".body-sidebar .section-item .sidebar-item-label, .body-sidebar .section-item .sidebar-item-icon, .body-sidebar .section-item .item-anchor",
            function(e) {
                // 如果点到了右侧控制按钮则忽略
                if ($(e.target).closest(".sidebar-item-control, .drop-icon").length) {
                    return;
                }

                e.preventDefault();
                e.stopPropagation();

                const $container = $(this).closest(".sidebar-item-container");
                const section_title = ($container.attr("item-name") || $container.attr("title") || "").trim();

                // 自动展开本菜单
                toggle_section($container, true);

                // 跳转到对应工作区
                const targetWs = SECTION_WORKSPACE_MAP[section_title];
                if (targetWs) {
                    try {
                        const currentRoute = (frappe.router && frappe.router.current_route) ? (frappe.get_route_str() || "") : "";
                        if (!currentRoute.includes(targetWs)) {
                            frappe.set_route("desk", targetWs);
                        }
                    } catch(err) {
                        console.error("Navigation error:", err);
                    }
                }
            }
        );
    }

    // 6. 注入视觉优化样式 (增强热区与 Hover 识别)
    function inject_dual_zone_styles() {
        if ($("#ashan-dual-zone-style").length) return;
        const styleHtml = `
        <style id="ashan-dual-zone-style">
            /* 一级分类标题加粗与热区优化 */
            .body-sidebar .section-item .standard-sidebar-item .item-anchor {
                cursor: pointer !important;
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                border-radius: var(--border-radius, 6px);
                transition: background-color 0.15s ease;
                padding-right: 4px !important;
            }
            .body-sidebar .section-item .standard-sidebar-item .item-anchor:hover {
                background-color: rgba(0, 0, 0, 0.04);
            }
            .body-sidebar .section-item .sidebar-item-label {
                font-weight: 700 !important;
                font-size: 13.5px !important;
                color: var(--text-color, #1f272e) !important;
                flex: 1 !important;
                padding-left: 4px;
                cursor: pointer !important;
            }
            .body-sidebar .section-item .sidebar-item-label:hover {
                color: var(--primary-color, #2f54eb) !important;
            }
            /* 右侧折叠箭头独立热区与按钮样式 */
            .body-sidebar .section-item .sidebar-item-control {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                margin-left: auto !important;
                z-index: 5;
            }
            .body-sidebar .section-item .sidebar-item-control .drop-icon {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: 28px !important;
                height: 28px !important;
                border-radius: 4px !important;
                cursor: pointer !important;
                transition: background-color 0.15s ease, transform 0.15s ease;
            }
            .body-sidebar .section-item .sidebar-item-control .drop-icon:hover {
                background-color: rgba(0, 0, 0, 0.1) !important;
            }
            /* 二级菜单严格去图标并缩进 */
            .body-sidebar .sidebar-child-item .sidebar-item-icon {
                display: none !important;
            }
            .body-sidebar .sidebar-child-item .standard-sidebar-item .item-anchor {
                padding-left: 24px !important;
                font-size: 13px !important;
                font-weight: 400 !important;
            }
        </style>
        `;
        $("head").append(styleHtml);
    }

    // 7. 监听 sidebar 渲染事件
    function setup_sidebar_state_restore() {
        $(document).on("sidebar_setup", function() {
            inject_dual_zone_styles();
            setup_dual_zone_handlers();
            setTimeout(restore_sidebar_states, 150);
        });

        if (window.frappe && frappe.router) {
            frappe.router.on("change", function() {
                inject_dual_zone_styles();
                setup_dual_zone_handlers();
                setTimeout(restore_sidebar_states, 250);
            });
        }
    }

    // 8. 初始化
    function init() {
        if (window.frappe) {
            frappe.re_route = frappe.re_route || {};
            frappe.re_route[""] = "desk/my-business";
            frappe.re_route["desk"] = "desk/my-business";
            frappe.re_route["app"] = "desk/my-business";
            frappe.re_route["Workspaces"] = "desk/my-business";
            frappe.re_route["workspaces"] = "desk/my-business";
        }
        inject_dual_zone_styles();
        setup_dual_zone_handlers();
        setup_sidebar_state_restore();
        setTimeout(restore_sidebar_states, 350);
    }

    $(document).on("app_ready", init);
    $(document).ready(function() {
        if (window.frappe && frappe.boot) {
            init();
        }
    });
})();
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER_SSH, password=PASSWORD, timeout=10)

sftp = ssh.open_sftp()
with sftp.open('/tmp/ashan_cn_sidebar.js', 'wb') as f:
    f.write(PERFECT_JS.encode('utf-8'))
sftp.close()

cmd1 = "docker cp /tmp/ashan_cn_sidebar.js erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/public/js/ashan_cn_sidebar.js"
cmd2 = "docker cp /tmp/ashan_cn_sidebar.js erpnext16:/home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js"
ssh.exec_command(cmd1)[1].channel.recv_exit_status()
ssh.exec_command(cmd2)[1].channel.recv_exit_status()

# Clear cache
cmd3 = "docker exec -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache"
ssh.exec_command(cmd3)[1].channel.recv_exit_status()
print("[OK] Deployed perfect dual zone script")

ssh.close()

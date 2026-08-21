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

UPDATED_JS = """/* ==========================================================================
   ERPNext 16 业务扩展 - 侧边栏专属修复与全链路默认路由
   ========================================================================== */

(function() {
    // 0. 路由全局重定向规则（根路径与空路径直达 my-business 看板）
    if (window.frappe) {
        frappe.re_route = frappe.re_route || {};
        frappe.re_route[""] = "desk/my-business";
        frappe.re_route["desk"] = "desk/my-business";
        frappe.re_route["app"] = "desk/my-business";
    }

    // 1. 一级标题 → 对应 Workspace 映射（点击跳转右侧 Dashboard）
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
        localStorage.setItem(ASHAN_SIDEBAR_KEY, JSON.stringify(state));
    }

    function get_section_state(section_title) {
        let state = get_sidebar_state();
        return state.hasOwnProperty(section_title) ? state[section_title] : false;
    }

    // 4. 将 masterSidebar 广播到所有 alias workspace（通过 items.length >= 25 智能定位）
    function sync_boot_sidebar_items() {
        if (!window.frappe || !frappe.boot || !frappe.boot.workspace_sidebar_item) return;

        let masterSidebar = null;
        for (let k in frappe.boot.workspace_sidebar_item) {
            let sb = frappe.boot.workspace_sidebar_item[k];
            if (sb && sb.items && sb.items.length >= 25) {
                masterSidebar = sb;
                break;
            }
        }

        if (masterSidebar) {
            for (let k in frappe.boot.workspace_sidebar_item) {
                let lk = k.toLowerCase();
                if (lk.includes('business') || lk.includes('stock') || lk.includes('procure') || 
                    lk.includes('fuel') || lk.includes('compliance') || lk.includes('account') || 
                    lk.includes('ashan') || lk.includes('业务') || lk.includes('库存') || 
                    lk.includes('采购') || lk.includes('财务') || lk.includes('车油') || lk.includes('合规')) {
                    frappe.boot.workspace_sidebar_item[k] = masterSidebar;
                }
            }
            const aliases = [
                "ashan cn procurement",
                "ashan_cn_procurement",
                "stock and inventory",
                "stock-and-inventory",
                "procurement management",
                "procurement-management",
                "vehicle fuel hub",
                "vehicle-fuel-hub",
                "company compliance center",
                "company-compliance-center",
                "accounting and finance",
                "accounting-and-finance",
                "my business",
                "my-business"
            ];
            aliases.forEach(key => {
                frappe.boot.workspace_sidebar_item[key] = masterSidebar;
            });

            // 重新刷新 sidebar 视图
            if (frappe.app && frappe.app.sidebar) {
                const currentTitle = frappe.app.sidebar.sidebar_title;
                if (!currentTitle || currentTitle.toLowerCase() === 'my business' || currentTitle.toLowerCase() === 'my-business') {
                    if (!frappe.app.sidebar.sidebar_data || !frappe.app.sidebar.sidebar_data.items || frappe.app.sidebar.sidebar_data.items.length < 25) {
                        frappe.app.sidebar.setup(masterSidebar.title || "业务扩展");
                    }
                }
            }
        }
    }

    // 5. 恢复侧边栏各 section 的折叠/展开状态
    function restore_sidebar_states() {
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
            const $children = $container.find(".sidebar-item-children");
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
    }

    // 6. 拦截 section 点击
    function setup_section_click_handler() {
        $(document).off("click.ashan_nav").on(
            "click.ashan_nav",
            ".body-sidebar .section-item .standard-sidebar-item",
            function(e) {
                const $container = $(this).closest(".sidebar-item-container");
                const section_title = (
                    $container.attr("item-name") ||
                    $container.attr("title") ||
                    ""
                ).trim();

                if (!section_title) return;

                setTimeout(function() {
                    const $children = $container.find(".sidebar-item-children");
                    const is_collapsed = $children.attr("data-state") === "closed";
                    set_section_state(section_title, is_collapsed);
                }, 50);

                const targetWs = SECTION_WORKSPACE_MAP[section_title];
                if (targetWs) {
                    const currentRoute = frappe.get_route_str() || "";
                    if (!currentRoute.includes(targetWs)) {
                        frappe.set_route("desk", targetWs);
                    }
                }
            }
        );
    }

    // 7. 覆盖 Frappe 原生 save_section_break_state
    function patch_frappe_sidebar_item() {
        if (!window.frappe || !frappe.ui || !frappe.ui.sidebar_item) return;
        if (frappe.ui.sidebar_item._ashan_patched) return;

        const TypeSectionBreak = frappe.ui.sidebar_item.TypeSectionBreak;
        if (!TypeSectionBreak || !TypeSectionBreak.prototype) return;

        const _orig_save = TypeSectionBreak.prototype.save_section_break_state;
        TypeSectionBreak.prototype.save_section_break_state = function() {
            const sidebarDataTitle = ($(".body-sidebar").attr("data-title") || "").toLowerCase();
            const knownOurSidebars = [
                "业务扩展", "ashan", "stock", "procurement",
                "fuel", "compliance", "accounting", "business"
            ];
            const isOurSidebar = knownOurSidebars.some(k => sidebarDataTitle.includes(k));

            if (isOurSidebar) {
                const title = (this.wrapper.attr("title") || this.wrapper.attr("item-name") || "").trim();
                if (title) {
                    set_section_state(title, this.collapsed);
                }
                return;
            }
            if (_orig_save) _orig_save.call(this);
        };

        frappe.ui.sidebar_item._ashan_patched = true;
    }

    // 8. 默认路由检查
    function check_default_route() {
        if (window.frappe && frappe.get_route_str) {
            const route = (frappe.get_route_str() || "").toLowerCase();
            if (!route || route === "" || route === "desk" || route === "app") {
                frappe.set_route("desk", "my-business");
            }
        }
    }

    // 9. 监听 sidebar 渲染事件
    function setup_sidebar_state_restore() {
        $(document).on("sidebar_setup", function() {
            setTimeout(restore_sidebar_states, 150);
        });

        if (window.frappe && frappe.router) {
            frappe.router.on("change", function() {
                sync_boot_sidebar_items();
                setTimeout(restore_sidebar_states, 250);
            });
        }
    }

    // 10. 初始化
    function init() {
        if (window.frappe) {
            frappe.re_route = frappe.re_route || {};
            frappe.re_route[""] = "desk/my-business";
            frappe.re_route["desk"] = "desk/my-business";
            frappe.re_route["app"] = "desk/my-business";
        }
        sync_boot_sidebar_items();
        patch_frappe_sidebar_item();
        setup_section_click_handler();
        setup_sidebar_state_restore();
        check_default_route();
        setTimeout(restore_sidebar_states, 400);
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
    f.write(UPDATED_JS.encode('utf-8'))
sftp.close()

cmd1 = "docker cp /tmp/ashan_cn_sidebar.js erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/public/js/ashan_cn_sidebar.js"
cmd2 = "docker cp /tmp/ashan_cn_sidebar.js erpnext16:/home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js"
ssh.exec_command(cmd1)[1].channel.recv_exit_status()
ssh.exec_command(cmd2)[1].channel.recv_exit_status()

# Clear cache
cmd3 = "docker exec -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache"
ssh.exec_command(cmd3)[1].channel.recv_exit_status()
print("[OK] Successfully deployed UTF-8 sidebar.js and cleared cache")

ssh.close()

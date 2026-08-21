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

UPDATED_JS = r"""/* ==========================================================================
   ERPNext 16 业务扩展 - 侧边栏专属修复与全链路默认路由
   功能：
   1. 一级标题（如"仓库与库存"）展开菜单 + 右侧切换专属 Dashboard 页
   2. 统一切换后各分类看板始终显示统一的一级/二级导航
   3. 修复 section-breaks-state 互相干扰 Bug（各分组展开状态独立存储）
   4. 登录 / 访问根路径自动平滑切入 /desk/my-business 专属主控台（杜绝 404 弹窗）
   ========================================================================== */

(function() {
    // ============================================================
    // 0. 路由全局重定向规则（根路径与空路径直达 my-business 看板）
    // ============================================================
    if (window.frappe) {
        frappe.re_route = frappe.re_route || {};
        frappe.re_route[""] = "desk/my-business";
        frappe.re_route["desk"] = "desk/my-business";
        frappe.re_route["app"] = "desk/my-business";
    }

    // ============================================================
    // 1. 一级标题 → 对应 Workspace 映射（点击跳转右侧 Dashboard）
    // ============================================================
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

    // ============================================================
    // 2. 我们自定义 Sidebar 的固定 key（用于 localStorage 隔离）
    // ============================================================
    const ASHAN_SIDEBAR_KEY = "ashan-cn-sidebar-state";

    // ============================================================
    // 3. 读/写 sidebar 折叠状态（完全独立于 Frappe 原生 localStorage）
    // ============================================================
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

    // ============================================================
    // 4. 将 masterSidebar 广播到所有 alias workspace，防止 sidebar 切换
    // ============================================================
    function sync_boot_sidebar_items() {
        if (!window.frappe || !frappe.boot || !frappe.boot.workspace_sidebar_item) return;

        let masterSidebar = null;
        for (let k in frappe.boot.workspace_sidebar_item) {
            let sb = frappe.boot.workspace_sidebar_item[k];
            if (sb && (
                k === "业务扩展" ||
                k === "ashan cn procurement" ||
                (sb.label && (sb.label === "业务扩展" || sb.label === "Ashan CN Procurement"))
            )) {
                masterSidebar = sb;
                break;
            }
        }

        if (masterSidebar) {
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
        }
    }

    // ============================================================
    // 5. 恢复侧边栏各 section 的折叠/展开状态
    // ============================================================
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

    // ============================================================
    // 6. 拦截 section 点击：保存我们自己的状态，同时跳转右侧看板
    // ============================================================
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

                // 延迟读取 DOM 实际折叠状态（原生 toggle 先执行）
                setTimeout(function() {
                    const $children = $container.find(".sidebar-item-children");
                    const is_collapsed = $children.attr("data-state") === "closed";
                    set_section_state(section_title, is_collapsed);
                }, 50);

                // 点击后跳转右侧对应看板（SPA 无刷新）
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

    // ============================================================
    // 7. 覆盖 Frappe 原生 save_section_break_state
    //    防止污染原生 "section-breaks-state" localStorage key
    // ============================================================
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

    // ============================================================
    // 8. 默认路由检查：若进入 /desk 或未指定工作区，自动进入 my-business
    // ============================================================
    function check_default_route() {
        if (window.frappe && frappe.get_route_str) {
            const route = (frappe.get_route_str() || "").toLowerCase();
            if (!route || route === "" || route === "desk" || route === "app") {
                frappe.set_route("desk", "my-business");
            }
        }
    }

    // ============================================================
    // 9. 监听 sidebar 渲染完成事件，恢复各 section 折叠状态
    // ============================================================
    function setup_sidebar_state_restore() {
        $(document).on("sidebar_setup", function() {
            setTimeout(restore_sidebar_states, 150);
        });

        if (window.frappe && frappe.router) {
            frappe.router.on("change", function() {
                setTimeout(restore_sidebar_states, 250);
            });
        }
    }

    // ============================================================
    // 10. 初始化
    // ============================================================
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
with sftp.open('/tmp/ashan_cn_sidebar.js', 'w') as f:
    f.write(UPDATED_JS)
sftp.close()

cmd1 = "docker cp /tmp/ashan_cn_sidebar.js erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/public/js/ashan_cn_sidebar.js"
cmd2 = "docker cp /tmp/ashan_cn_sidebar.js erpnext16:/home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js"
ssh.exec_command(cmd1)[1].channel.recv_exit_status()
ssh.exec_command(cmd2)[1].channel.recv_exit_status()

# Clear cache
cmd3 = "docker exec -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache"
ssh.exec_command(cmd3)[1].channel.recv_exit_status()
print("[OK] Uploaded updated sidebar.js and cleared cache")

ssh.close()

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

NATIVE_INTEGRATED_JS = """/* ==========================================================================
   ERPNext 16 业务扩展 - 深度集成 Frappe TypeSectionBreak 原生架构
   - 彻底重构事件监听器：
     1. 右侧箭头按钮：纯粹执行原生 toggle() 展开/折叠，0 延迟、0 竞争、不跳路由
     2. 左侧文字区域：直达对应 Workspace Dashboard，并自动确保展开当前菜单
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

    // 2. 深度重写 Frappe 原生 TypeSectionBreak 原型方法
    function patch_native_section_break() {
        if (!window.frappe || !frappe.ui || !frappe.ui.sidebar_item || !frappe.ui.sidebar_item.TypeSectionBreak) {
            return false;
        }

        const TypeSectionBreak = frappe.ui.sidebar_item.TypeSectionBreak;
        if (TypeSectionBreak._ashan_deep_patched) return true;

        // 重写 toggle：彻底修复 .hidden 与 icon 图标对应关系
        TypeSectionBreak.prototype.toggle = function() {
            if (this.collapsed) {
                if (this.$drop_icon) {
                    this.$drop_icon.attr("data-state", "closed").find("use").attr("href", "#icon-chevron-right");
                }
                $(this.wrapper).attr("data-state", "closed");
                if (this.$nested_items) {
                    $(this.$nested_items).addClass("hidden").hide();
                }
            } else {
                if (this.$drop_icon) {
                    this.$drop_icon.attr("data-state", "opened").find("use").attr("href", "#icon-chevron-down");
                }
                $(this.wrapper).attr("data-state", "opened");
                if (this.$nested_items) {
                    $(this.$nested_items).removeClass("hidden").show();
                }
            }
        };

        // 彻底重构事件绑定：职责严格解耦
        TypeSectionBreak.prototype.setup_event_listner = function() {
            const me = this;
            const $standardItem = $(this.wrapper.find(".standard-sidebar-item")[0]);
            if (!$standardItem.length) return;

            // 解除所有历史冲突监听
            $standardItem.off("click");

            // [区域 1]：右侧折叠箭头独立按钮点击 -> 纯粹折叠/展开
            this.wrapper.find(".sidebar-item-control, .drop-icon").off("click").on("click", function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (e.stopImmediatePropagation) e.stopImmediatePropagation();
                me.collapsed = !me.collapsed;
                me.toggle();
                me.save_section_break_state();
            });

            // [区域 2]：左侧文字与图标区域点击 -> 跳转工作区看板 + 自动展开
            this.wrapper.find(".sidebar-item-label, .sidebar-item-icon, .item-anchor").off("click").on("click", function(e) {
                if ($(e.target).closest(".sidebar-item-control, .drop-icon").length) return;

                e.preventDefault();
                e.stopPropagation();

                // 自动展开本分类
                if (me.collapsed) {
                    me.collapsed = false;
                    me.toggle();
                    me.save_section_break_state();
                }

                // 跳转对应 Workspace
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

        TypeSectionBreak._ashan_deep_patched = true;
        return true;
    }

    // 3. 注入高响应度双区样式
    function inject_styles() {
        if ($("#ashan-native-dual-zone-style").length) return;
        const styleHtml = `
        <style id="ashan-native-dual-zone-style">
            /* 一级分类标题加粗与热区 */
            .body-sidebar .section-item .standard-sidebar-item .item-anchor {
                cursor: pointer !important;
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                border-radius: var(--border-radius, 6px);
                transition: background-color 0.1s ease;
                padding: 4px 8px !important;
            }
            .body-sidebar .section-item .standard-sidebar-item .item-anchor:hover {
                background-color: rgba(0, 0, 0, 0.05);
            }
            .body-sidebar .section-item .sidebar-item-label {
                font-weight: 700 !important;
                font-size: 13.5px !important;
                color: var(--text-color, #1f272e) !important;
                flex: 1 !important;
                cursor: pointer !important;
                user-select: none;
            }
            .body-sidebar .section-item .sidebar-item-label:hover {
                color: var(--primary-color, #2f54eb) !important;
            }
            /* 右侧独立箭头按钮 */
            .body-sidebar .section-item .sidebar-item-control {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                margin-left: auto !important;
                z-index: 10;
            }
            .body-sidebar .section-item .sidebar-item-control .drop-icon {
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                width: 28px !important;
                height: 28px !important;
                border-radius: 4px !important;
                cursor: pointer !important;
                transition: background-color 0.1s ease;
                pointer-events: auto !important;
            }
            .body-sidebar .section-item .sidebar-item-control .drop-icon:hover {
                background-color: rgba(0, 0, 0, 0.12) !important;
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

    // 4. 初始化挂载
    function init() {
        inject_styles();
        patch_native_section_break();

        // 监听侧边栏每次重新构建
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
"""

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, port=PORT, username=USER_SSH, password=PASSWORD, timeout=10)

sftp = ssh.open_sftp()
with sftp.open('/tmp/ashan_cn_sidebar.js', 'wb') as f:
    f.write(NATIVE_INTEGRATED_JS.encode('utf-8'))
sftp.close()

cmd1 = "docker cp /tmp/ashan_cn_sidebar.js erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/public/js/ashan_cn_sidebar.js"
cmd2 = "docker cp /tmp/ashan_cn_sidebar.js erpnext16:/home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js"
ssh.exec_command(cmd1)[1].channel.recv_exit_status()
ssh.exec_command(cmd2)[1].channel.recv_exit_status()

# Clear cache
cmd3 = "docker exec -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache"
ssh.exec_command(cmd3)[1].channel.recv_exit_status()
print("[OK] Deployed Frappe Native Integrated TypeSectionBreak architecture!")

ssh.close()

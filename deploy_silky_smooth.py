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

SILKY_SMOOTH_JS = """/* ==========================================================================
   ERPNext 16 业务扩展 - 丝滑双向展开/折叠与全联动架构 (Silky Smooth Toggle)
   - 点击右侧小箭头：丝滑平滑展开/收起 (0.2s 缓动)，不跳路由
   - 点击左侧文字区：丝滑展开/折叠切换 + 联动加载对应分类 Dashboard 页面
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
        if (TypeSectionBreak._ashan_silky_patched) return true;

        // 丝滑动画切换 toggle()
        TypeSectionBreak.prototype.toggle = function(animate = true) {
            const me = this;
            const $nested = $(this.$nested_items);
            if (!$nested.length) return;

            // 移除可能阻断动画的强制 hidden 类
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

        // 绑定事件：右侧箭头纯动画，左侧文字兼顾动画与跳转
        TypeSectionBreak.prototype.setup_event_listner = function() {
            const me = this;
            const $standardItem = $(this.wrapper.find(".standard-sidebar-item")[0]);
            if (!$standardItem.length) return;

            $standardItem.off("click");

            // [1] 右侧小箭头点击 -> 纯粹丝滑折叠/展开
            this.wrapper.find(".sidebar-item-control, .drop-icon").off("click").on("click", function(e) {
                e.preventDefault();
                e.stopPropagation();
                if (e.stopImmediatePropagation) e.stopImmediatePropagation();
                me.collapsed = !me.collapsed;
                me.toggle(true);
                me.save_section_break_state();
            });

            // [2] 左侧文字与图标区域点击 -> 丝滑折叠/展开切换 + 联动页面跳转
            this.wrapper.find(".sidebar-item-label, .sidebar-item-icon, .item-anchor").off("click").on("click", function(e) {
                if ($(e.target).closest(".sidebar-item-control, .drop-icon").length) return;

                e.preventDefault();
                e.stopPropagation();

                // 丝滑展开/折叠切换
                me.collapsed = !me.collapsed;
                me.toggle(true);
                me.save_section_break_state();

                // 联动跳转至对应分类 Dashboard (如果尚未在该页面)
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

        TypeSectionBreak._ashan_silky_patched = true;
        return true;
    }

    // 3. 注入丝滑平滑样式
    function inject_styles() {
        if ($("#ashan-silky-smooth-style").length) return;
        const styleHtml = `
        <style id="ashan-silky-smooth-style">
            /* 一级分类标题加粗与平滑过渡 */
            .body-sidebar .section-item .standard-sidebar-item .item-anchor {
                cursor: pointer !important;
                display: flex !important;
                align-items: center !important;
                justify-content: space-between !important;
                border-radius: var(--border-radius, 6px);
                transition: background-color 0.15s ease;
                padding: 4px 8px !important;
                user-select: none;
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
                transition: color 0.15s ease;
            }
            .body-sidebar .section-item .sidebar-item-label:hover {
                color: var(--primary-color, #2f54eb) !important;
            }
            /* 右侧独立小箭头样式 */
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
                transition: background-color 0.15s ease, transform 0.15s ease;
                pointer-events: auto !important;
            }
            .body-sidebar .section-item .sidebar-item-control .drop-icon:hover {
                background-color: rgba(0, 0, 0, 0.12) !important;
            }
            /* 二级菜单动画与缩进 */
            .body-sidebar .nested-container {
                will-change: height;
            }
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
    f.write(SILKY_SMOOTH_JS.encode('utf-8'))
sftp.close()

cmd1 = "docker cp /tmp/ashan_cn_sidebar.js erpnext16:/home/frappe/frappe-bench/apps/ashan_cn_procurement/ashan_cn_procurement/public/js/ashan_cn_sidebar.js"
cmd2 = "docker cp /tmp/ashan_cn_sidebar.js erpnext16:/home/frappe/frappe-bench/sites/assets/ashan_cn_procurement/js/ashan_cn_sidebar.js"
ssh.exec_command(cmd1)[1].channel.recv_exit_status()
ssh.exec_command(cmd2)[1].channel.recv_exit_status()

# Clear cache
cmd3 = "docker exec -w /home/frappe/frappe-bench erpnext16 bench --site site1.local clear-cache"
ssh.exec_command(cmd3)[1].channel.recv_exit_status()
print("[OK] Deployed Silky Smooth Toggle to container!")

ssh.close()

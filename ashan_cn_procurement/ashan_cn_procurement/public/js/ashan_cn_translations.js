/* ==========================================================================
   ERPNext 16 业务扩展 - 全站日常操作页面高级中文汉化补全与本地化增强
   (Comprehensive Daily Operations Chinese Localization & Translation Engine)
   ========================================================================== */

(function() {
    const CN_TRANSLATIONS = {
        // === 1. 顶部栏、导航与系统基础操作 ===
        "Search or type a command (Ctrl + K)": "搜索单据、页面或输入快捷指令 (Ctrl + K)",
        "Search": "搜索",
        "Notification": "通知中心",
        "Notifications": "通知中心",
        "Home": "首页",
        "User": "用户与账号",
        "Role": "角色与岗位",
        "Permissions": "权限配置",
        "User Permission": "用户数据权限",
        "Permission Manager": "角色权限管理器",
        "Permission Inspector": "权限检查器",
        "Role Permissions Manager": "角色权限管理器",
        "Set User Permissions": "设置用户权限",
        "Audits": "审计与日志",
        "Activity Log": "操作动态日志",
        "Permission Log": "权限变更日志",
        "Access Log": "系统访问日志",
        "Settings": "系统设置",
        "System Settings": "全局系统设置",
        "My Settings": "个人设置",
        "Log out": "退出登录",
        "Switch to standard": "切换至标准界面",
        "Toggle Full Width": "切换全屏/等宽",
        "Session Expired": "会话已过期",
        "Please login again": "请重新登录系统",
        "Logged In": "登录成功",
        "Invalid login credentials": "账号或密码错误",
        "Not permitted": "无访问权限",
        "Not found": "未找到请求的页面",
        "The resource you are looking for is not available": "您访问的资源不存在或已被移动",
        "You do not have enough permissions to access this resource. Please contact your manager to get access.": "您没有足够的权限访问此资源，请联系管理员为您配置权限。",

        // === 2. 列表视图 (List View)、筛选与排序 ===
        "List View": "列表视图",
        "Report View": "报表视图",
        "Dashboard View": "仪表盘看板",
        "Kanban": "看板视图",
        "Gantt": "甘特图",
        "Calendar": "日历视图",
        "Image View": "卡片图库",
        "Saved Filters": "已存常用筛选",
        "Filter": "筛选",
        "Filters": "筛选条件",
        "Filter By": "筛选条件",
        "Add Filter": "+ 添加筛选条件",
        "Clear Filters": "清空全部筛选",
        "Sort By": "排序规则",
        "Created On": "创建时间",
        "Modified On": "修改时间",
        "Created By": "创建人",
        "Modified By": "修改人",
        "Descending": "降序 (最新优先)",
        "Ascending": "升序 (最早优先)",
        "Load More": "加载更多记录",
        "Refresh": "刷新数据",
        "Select All": "全选当前页",
        "Unselect All": "取消全选",
        "Showing {0} to {1} of {2}": "显示第 {0} 至 {1} 项，共 {2} 项",
        "of": "项，共",
        "No matching records found": "未找到符合条件的单据记录",
        "No Data": "暂无数据",

        // === 3. 表单操作与按钮 (Form Actions & Buttons) ===
        "Actions": "操作 ▾",
        "Action": "操作",
        "Save": "保存单据",
        "Saved": "已保存",
        "Not Saved": "未保存修改",
        "Discard": "放弃修改",
        "Submit": "提交单据",
        "Cancel": "作废单据",
        "Amend": "修改重开",
        "Delete": "删除单据",
        "Permanently Delete": "永久删除",
        "Delete permanently": "永久删除",
        "Duplicate": "复制新建",
        "Print": "打印单据",
        "Email": "发送邮件",
        "Upload": "上传文件",
        "Download": "下载附件",
        "Add row": "+ 添加行",
        "Add Row": "+ 添加行",
        "Add multiple": "+ 批量添加行",
        "Insert Above": "在上方插入行",
        "Insert Below": "在下方插入行",
        "Move Up": "上移",
        "Move Down": "下移",
        "Delete Row": "删除行",
        "Confirm": "确认执行",
        "Close": "关闭窗口",
        "Edit": "编辑修改",
        "New": "新建",
        "Create": "创建",
        "+ Add": "+ 新建",
        "+ New": "+ 新建",
        "+ Add Role": "+ 新建角色",
        "+ Add User": "+ 新建用户",

        // === 4. 单据状态 (Document Statuses) ===
        "Draft": "草稿",
        "Submitted": "已提交",
        "Cancelled": "已作废",
        "Pending": "待处理",
        "Approved": "已批准",
        "Rejected": "已驳回",
        "Open": "进行中",
        "Closed": "已结案",
        "Paid": "已支付",
        "Unpaid": "未付款",
        "Overdue": "已逾期",
        "Partly Paid": "部分付款",
        "To Bill": "待开票",
        "To Receive": "待入库",
        "To Deliver": "待出库",
        "Completed": "已完成",
        "Active": "启用",
        "Disabled": "已停用",
        "Enabled": "已启用",
        "Unbilled": "未开票",
        "Billed": "已开票",
        "Return": "退货/退款",

        // === 5. 权限配置专项翻译 (Permission Manager) ===
        "Select Document Type or Role to start.": "请在上方选择【单据类型】或【角色】以开始配置权限规则。",
        "Quick Help for Setting Permissions:": "权限配置快速指南：",
        "Meaning of Different Permission Types:": "各类权限类型业务释义与应用场景：",
        "Document Type": "单据类型 (DocType)",
        "Roles": "角色清单",
        "Select": "选择查看 (Select)",
        "Read": "读取详情 (Read)",
        "Write": "编辑修改 (Write)",
        "Create": "新建单据 (Create)",
        "Delete": "删除单据 (Delete)",
        "Submit": "提交审核 (Submit)",
        "Cancel": "作废撤销 (Cancel)",
        "Amend": "重开修改 (Amend)",
        "Report": "生成报表 (Report)",
        "Export": "导出数据 (Export)",
        "Import": "批量导入 (Import)",
        "Share": "共享单据 (Share)",
        "Print": "打印单据 (Print)",
        "Email": "邮件发送 (Email)",
        "User Permissions": "按用户隔离数据权限",
        "If Owner": "仅限创建者本人",
        "Permissions are set on Roles and Document Types (called DocTypes) by setting rights like Read, Write, Create, Delete, Submit, Cancel, Amend, Report, Import, Export, Print, Email and Set User Permissions.": "权限基于【角色】与【单据类型】进行配置，包含读取、写入、新建、删除、提交、作废、修改重开、报表、导入导出、打印、邮件及用户数据权限隔离。",
        "Permissions get applied on Users based on what Roles they are assigned.": "系统会根据为用户分配的角色，自动将相应权限应用到该用户。",
        "Roles can be set for users from their User page. Setup > User": "可以在【用户与账号】页面为具体用户勾选并分配角色。",
        "The system provides many pre-defined roles. You can add new roles to set finer permissions. Add a New Role": "系统提供了丰富的预置标准角色，您也可以添加自定义角色进行更精细的权限划分。",
        "Permissions are automatically applied to Standard Reports and searches.": "配置的权限会自动应用到标准报表与全局搜索中。",
        "As a best practice, do not assign the same set of permission rule to different Roles. Instead, set multiple Roles to the same User.": "最佳实践建议：不要为不同角色配置完全相同的规则，建议为一个用户分配多个不同职能的角色。",
        "Allows the user to search and see records.": "允许用户搜索并查看单据摘要记录。",
        "The user can select a Customer in Sales Order but cannot open the Customer master.": "例如：用户可在订单中选择客户，但无法查看客户详细档案。",
        "Allows the user to view the document.": "允许用户打开并查看单据的完整详情。",
        "The user can view Sales Invoices but cannot modify any field values in them.": "例如：用户可查看发票详情，但无法修改其中的任何字段。",
        "Allows the user to edit existing records they have access to.": "允许用户编辑并修改已有单据。",
        "The user can update a customer or any other fields in an existing Sales Order but cannot create a new Sales Order.": "例如：用户可修改订单内容，但无法新建订单。",
        "Allows the user to create new records.": "允许用户创建新单据。",
        "Allows the user to delete records they have access to.": "允许用户删除单据。",
        "Allows the user to submit documents.": "允许用户提交审核单据。",
        "Allows the user to cancel submitted documents.": "允许用户作废已提交的单据。",
        "Allows the user to amend cancelled documents.": "允许用户基于已作废单据重开修改。",

        // === 6. 采购、仓库、报销与油卡业务术语 ===
        "Purchase Order": "采购订单",
        "Purchase Receipt": "采购入库单",
        "Purchase Invoice": "采购发票",
        "Supplier": "供应商档案",
        "Supplier Name": "供应商名称",
        "Supplier Group": "供应商分类",
        "Item": "物料主数据",
        "Item Code": "物料编码",
        "Item Name": "物料名称",
        "Item Group": "物料分类",
        "Item Type": "物料类型",
        "Service": "服务类",
        "Sales & Purchase": "销售与采购",
        "Series": "编号系列",
        "Last Updated On": "最后更新时间",
        "+ Add {0}": "+ 新建 {0}",
        "Add {0}": "+ 新建 {0}",
        "Stock Entry": "物料调拨与出入库",
        "Delivery Note": "销售出库单",
        "Stock Ledger": "库存台账明细",
        "Warehouse": "仓库",
        "Default Warehouse": "默认仓库",
        "Quantity": "数量",
        "Qty": "数量",
        "Rate": "含税单价",
        "Amount": "金额 (¥)",
        "Grand Total": "总计金额 (¥)",
        "Net Total": "不含税净额 (¥)",
        "Total Quantity": "总数量",
        "Taxes and Charges": "税费与附加项",
        "Tax Rate": "税率 %",
        "Tax Amount": "税额 (¥)",
        "Reimbursement Request": "报销申请单",
        "Expense Claim": "费用报销单",
        "Payment Entry": "付款凭证",
        "Journal Entry": "日记账凭证",
        "Oil Card": "油卡档案",
        "Oil Card Ledger": "油卡综合台账明细台",
        "Oil Card Refuel Log": "车辆加油明细表",
        "Oil Card Recharge Log": "油卡充值明细表",
        "Oil Card Monthly Closing": "油卡月度能耗汇总",
        "Vehicle Archive": "车辆档案",
        "Oil Card Manager": "油卡管理员",
        "Oil Card Operator": "油卡操作员",
        "Stock Manager": "仓库管理员",
        "Purchase Manager": "采购管理员",
        "Accounts Manager": "财务主管",
        "Fleet Manager": "车队主管",
        "System Manager": "系统管理员"
    };

    // 1. 注入前端 Frappe 翻译字典
    if (window.frappe) {
        frappe.provide("frappe._messages");
        frappe._messages = frappe._messages || {};
        Object.assign(frappe._messages, CN_TRANSLATIONS);

        if (frappe.boot && frappe.boot.__messages) {
            Object.assign(frappe.boot.__messages, CN_TRANSLATIONS);
        }

        // 2. 增强 frappe.__ 国际化查找逻辑
        const originalTranslate = window.__;
        window.__ = function(txt, replace, context) {
            if (typeof txt === "string") {
                const trimmed = txt.trim();
                if (CN_TRANSLATIONS[trimmed]) {
                    let res = CN_TRANSLATIONS[trimmed];
                    if (replace && Array.isArray(replace)) {
                        replace.forEach((val, idx) => {
                            res = res.replace(new RegExp(`\\{${idx}\\}`, "g"), val);
                        });
                    }
                    return res;
                }
            }
            if (typeof originalTranslate === "function") {
                return originalTranslate(txt, replace, context);
            }
            return txt;
        };

        if (window.frappe.__) {
            window.frappe.__ = window.__;
        }
    }

    // 3. 动态扫描并汉化未包裹 __() 的原生 DOM 节点（如原生菜单项、未翻译面包屑等）
    function localize_dynamic_dom() {
        // 汉化 List View 状态、按钮和操作文字
        $(".btn:contains('Actions'), button:contains('Actions')").each(function() {
            if ($(this).children().length === 0 || $(this).find("svg, .icon").length > 0) {
                $(this).contents().filter(function() { return this.nodeType === 3 && this.nodeValue.trim() === "Actions"; }).replaceWith("操作 ▾");
            }
        });
        $(".btn:contains('Add Row'), button:contains('Add Row')").each(function() {
            $(this).contents().filter(function() { return this.nodeType === 3 && this.nodeValue.trim() === "Add Row"; }).replaceWith("+ 添加行");
        });
        $(".btn:contains('Add multiple'), button:contains('Add multiple')").each(function() {
            $(this).contents().filter(function() { return this.nodeType === 3 && this.nodeValue.trim() === "Add multiple"; }).replaceWith("+ 批量添加");
        });
    }

    $(document).ready(function() {
        localize_dynamic_dom();
        $(document).ajaxComplete(function() {
            setTimeout(localize_dynamic_dom, 100);
        });
    });
})();

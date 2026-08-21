frappe.pages["procurement-workflow"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("采购流程总览"),
        single_column: true,
    });

    const state = {
        company: frappe.defaults.get_user_default("Company") || "",
        companies: [],
        loading: false,
    };

    const $main = $(page.main);
    $main.html(`
        <div class="procurement-workflow-page">
            <div class="pw-toolbar">
                <div>
                    <div class="pw-title">标准采购工作流</div>
                    <div class="pw-subtitle">采购申请 → 采购订单 → 采购入库 → 采购发票 → 报销 / 付款</div>
                </div>
                <div class="pw-company-group">
                    <span class="pw-company-label">公司</span>
                    <div class="pw-company-options"></div>
                </div>
            </div>

            <div class="pw-notice">
                正常供应商付款由采购发票进入 Payment Entry；仅员工垫付或需报销的未付款采购发票进入报销申请。
            </div>

            <div class="pw-state pw-loading">正在读取采购流程状态…</div>
            <div class="pw-pipeline" style="display:none;"></div>

            <div class="pw-actions">
                <button class="btn btn-default btn-sm" data-route="Supplier">供应商档案</button>
                <button class="btn btn-default btn-sm" data-route="Item">物料主数据</button>
                <button class="btn btn-default btn-sm" data-route="Stock Entry">物料收发</button>
                <button class="btn btn-primary btn-sm" data-route="Payment Entry">付款凭证</button>
            </div>
        </div>
    `);

    const $companyOptions = $main.find(".pw-company-options");
    const $state = $main.find(".pw-state");
    const $pipeline = $main.find(".pw-pipeline");

    function money(value) {
        return format_currency(Number(value || 0), "CNY");
    }

    function escapeHtml(value) {
        return $("<div>").text(value == null ? "" : String(value)).html();
    }

    function setLoading(loading, message) {
        state.loading = loading;
        if (loading) {
            $pipeline.hide();
            $state
                .removeClass("pw-error")
                .addClass("pw-loading")
                .text(message || "正在读取采购流程状态…")
                .show();
        }
    }

    function renderCompanies() {
        $companyOptions.empty();
        state.companies.forEach((company) => {
            const active = company.name === state.company ? "active" : "";
            $companyOptions.append(`
                <button type="button"
                        class="pw-company-chip ${active}"
                        data-company="${escapeHtml(company.name)}">
                    ${escapeHtml(company.name)}
                </button>
            `);
        });
    }

    function renderStages(stages) {
        const html = (stages || []).map((stage, index) => {
            const amount = stage.amount === null || stage.amount === undefined
                ? ""
                : `<div class="pw-stage-amount">${money(stage.amount)}</div>`;
            const arrow = index < stages.length - 1
                ? `<div class="pw-arrow" aria-hidden="true">→</div>`
                : "";

            return `
                <div class="pw-stage-wrap">
                    <button type="button"
                            class="pw-stage-card"
                            data-doctype="${escapeHtml(stage.doctype)}">
                        <div class="pw-stage-number">${escapeHtml(stage.number)}</div>
                        <div class="pw-stage-label">${escapeHtml(stage.label)}</div>
                        <div class="pw-stage-metric">
                            <strong>${escapeHtml(stage.count)}</strong>
                            <span>${escapeHtml(stage.count_label)}</span>
                        </div>
                        ${amount}
                        <div class="pw-stage-open">打开列表</div>
                    </button>
                    ${arrow}
                </div>
            `;
        }).join("");

        $pipeline.html(html).show();
        $state.hide();
    }

    function loadSummary() {
        if (state.loading) return;
        setLoading(true);

        frappe.call({
            method: "ashan_cn_procurement.services.procurement_workflow.get_procurement_workflow_summary",
            args: { company: state.company || null },
            callback(r) {
                state.loading = false;
                const data = r.message || {};
                if (data.company && !state.company) {
                    state.company = data.company;
                    renderCompanies();
                }
                renderStages(data.stages || []);
            },
            error() {
                state.loading = false;
                $pipeline.hide();
                $state
                    .removeClass("pw-loading")
                    .addClass("pw-error")
                    .html(`读取失败。<button type="button" class="btn btn-xs btn-default pw-retry">重新加载</button>`)
                    .show();
            },
        });
    }

    function loadCompanies() {
        frappe.db.get_list("Company", {
            fields: ["name"],
            order_by: "name asc",
            limit: 50,
        }).then((rows) => {
            state.companies = rows || [];
            if (!state.company && state.companies.length) {
                state.company = state.companies[0].name;
            }
            renderCompanies();
            loadSummary();
        }).catch(() => {
            loadSummary();
        });
    }

    $main.on("click", ".pw-company-chip", function () {
        if (state.loading) return;
        state.company = $(this).data("company");
        renderCompanies();
        loadSummary();
    });

    $main.on("click", ".pw-stage-card", function () {
        const doctype = $(this).data("doctype");
        if (doctype) frappe.set_route("List", doctype, "List");
    });

    $main.on("click", ".pw-actions [data-route]", function () {
        frappe.set_route("List", $(this).data("route"), "List");
    });

    $main.on("click", ".pw-retry", loadSummary);

    page.set_secondary_action(__("刷新"), loadSummary, "refresh");
    loadCompanies();
};

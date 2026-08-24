// Copyright (c) 2026, Ashan CN Procurement and contributors

frappe.pages["material-request-workbench"].on_page_load = function (wrapper) {
    frappe.require([
        "/assets/ashan_cn_procurement/css/procurement_workbench.css?v=20260824.49",
        "/assets/ashan_cn_procurement/js/procurement_workbench.js?v=20260824.49",
    ], () => window.AshanProcurementWorkbench.mount(wrapper, "request"));
};

/* ==========================================================================
   采购发票列表页定制 (Purchase Invoice List View)
   ========================================================================== */

frappe.listview_settings['Purchase Invoice'] = {
    onload: function(listview) {
        listview.page.add_inner_button(__("🧾 选单创建发票"), function() {
            frappe.set_route("procurement-order-picker", "?stage=pi");
        });
    }
};

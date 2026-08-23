/* ==========================================================================
   采购申请列表页定制 (Material Request List View)
   ========================================================================== */

frappe.listview_settings['Material Request'] = {
    add_fields: ["custom_doc_details", "material_request_type", "schedule_date", "status"],

    onload: function(listview) {
        listview.page.add_inner_button(__("🛒 选单订货"), function() {
            frappe.set_route("procurement-order-picker", "?stage=po");
        });
    },

    formatters: {
        custom_doc_details: function(value, df, doc) {
            if (typeof ashan !== 'undefined' && ashan.doc_details && ashan.doc_details.render_badges) {
                return ashan.doc_details.render_badges(value);
            }
            return value || "";
        }
    }
};

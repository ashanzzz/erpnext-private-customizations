/* ==========================================================================
   物资入库单列表页定制 (Purchase Receipt List View)
   ========================================================================== */

frappe.listview_settings['Purchase Receipt'] = {
    add_fields: ["custom_doc_details", "supplier_name", "posting_date", "grand_total", "status"],

    formatters: {
        custom_doc_details: function(value, df, doc) {
            if (typeof ashan !== 'undefined' && ashan.doc_details && ashan.doc_details.render_badges) {
                return ashan.doc_details.render_badges(value);
            }
            return value || "";
        }
    }
};

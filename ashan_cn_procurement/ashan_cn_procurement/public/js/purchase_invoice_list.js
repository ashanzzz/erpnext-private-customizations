/* ==========================================================================
   采购发票列表页定制 (Purchase Invoice List View)
   ========================================================================== */

frappe.listview_settings['Purchase Invoice'] = {
    add_fields: ["custom_doc_details", "custom_items_summary", "supplier", "bill_no", "bill_date", "grand_total", "status"],

    formatters: {
        custom_doc_details: function(value, df, doc) {
            const val = value || (doc && doc.custom_items_summary);
            if (typeof ashan !== 'undefined' && ashan.doc_details && ashan.doc_details.render_badges) {
                return ashan.doc_details.render_badges(val);
            }
            return val || "";
        },
        custom_items_summary: function(value, df, doc) {
            const val = value || (doc && doc.custom_doc_details);
            if (typeof ashan !== 'undefined' && ashan.doc_details && ashan.doc_details.render_badges) {
                return ashan.doc_details.render_badges(val);
            }
            return val || "";
        }
    }
};

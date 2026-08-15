"""Auditable draft reservation for one Purchase Invoice item."""

from frappe.model.document import Document


class ReimbursementSourceReservation(Document):
    def validate(self):
        if self.status == "Released":
            self.active_source_key = None
        elif self.source_purchase_invoice_item:
            self.active_source_key = self.source_purchase_invoice_item

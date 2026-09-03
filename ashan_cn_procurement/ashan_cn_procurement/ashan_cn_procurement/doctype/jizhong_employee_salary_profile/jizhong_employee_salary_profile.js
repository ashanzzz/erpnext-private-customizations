// Copyright (c) 2026, Ashan and contributors
// For license information, please see license.txt

frappe.ui.form.on('Jizhong Employee Salary Profile', {
	refresh: function(frm) {
		calculate_deductions_total(frm);
	},
	deduction_child_education: function(frm) { calculate_deductions_total(frm); },
	deduction_continuing_education: function(frm) { calculate_deductions_total(frm); },
	deduction_serious_illness: function(frm) { calculate_deductions_total(frm); },
	deduction_housing_loan: function(frm) { calculate_deductions_total(frm); },
	deduction_housing_rent: function(frm) { calculate_deductions_total(frm); },
	deduction_elderly_care: function(frm) { calculate_deductions_total(frm); },
	deduction_infant_care: function(frm) { calculate_deductions_total(frm); }
});

function calculate_deductions_total(frm) {
	const total = flt(frm.doc.deduction_child_education) +
		flt(frm.doc.deduction_continuing_education) +
		flt(frm.doc.deduction_serious_illness) +
		flt(frm.doc.deduction_housing_loan) +
		flt(frm.doc.deduction_housing_rent) +
		flt(frm.doc.deduction_elderly_care) +
		flt(frm.doc.deduction_infant_care);
	frm.set_value('special_additional_deductions_total', total);
}

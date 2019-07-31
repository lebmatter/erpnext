from __future__ import unicode_literals
import frappe

def execute():

	transaction_time_and_date_and_set_time = ["Purchase Receipt", "Delivery Note", "Fees", "Stock Reconciliation", "Purchase Invoice",
		"Sales Invoice", "Stock Entry"]

	transaction_time_and_date = ["Stock Ledger Entry"]

	transaction_date = ["Landed Cost Purchase Receipt", "Expense Claim", "Expense Claim Advance", "Exchange Rate Revaluation",
		"Journal Entry", "Bank Reconciliation Detail", "Employee Advance", "Job Card", "Production Plan", "Payment Order", "Payroll Entry",
		"Payment Entry", "Invoice Discounting", "Discounted Invoice", "Salary Slip", "Payment Reconciliation Payment",
		"Loan", "Opening Invoice Creation Tool Item"]

	for doctype in transaction_time_and_date_and_set_time:
		frappe.db.sql(""" UPDATE `tab{doctype}` SET transaction_date = posting_date, transaction_time = posting_time,
			set_transaction_time = set_posting_time where transaction_date is NULL""".format(doctype=doctype))

	for doctype in transaction_time_and_date:
		frappe.db.sql(""" UPDATE `tab{doctype}` SET transaction_date = posting_date, transaction_time = posting_time where transaction_date is NULL""".format(doctype=doctype))

	for doctype in transaction_date:
		frappe.db.sql(""" UPDATE `tab{doctype}` SET transaction_date = posting_date where transaction_date is NULL""".format(doctype=doctype))
# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json
from frappe.utils.file_manager import save_file
from frappe.utils import flt

class GSTR3BReport(Document):
	pass

def get_data(company, address, month):

	report_dict = {
		"gstin": "",
		"ret_period": "",
		"inward_sup": {
			"isup_details": [
				{
					"ty": "GST",
					"intra": 0,
					"inter": 0
				},
				{
					"ty": "NONGST",
					"inter": 0,
					"intra": 0
				}
			]
		},
		"sup_details": {
			"osup_zero": {
				"csamt": 0,
				"txval": 0,
				"iamt": 0
			},
			"osup_nil_exmp": {
				"txval": 0,
				"iamt": 0,
				"camt": 0,
				"samt": 0,
				"csamt": 0
			},
			"osup_det": {
				"samt": 0,
				"csamt": 0,
				"txval": 0,
				"camt": 0,
				"iamt": 0
			},
			"isup_rev": {
				"samt": 0,
				"csamt": 0,
				"txval": 0,
				"camt": 0,
				"iamt": 0
			},
			"osup_nongst": {
				"txval": 0,
				"iamt": 0,
				"camt": 0,
				"samt": 0,
				"csamt": 0
			}
		},
		"inter_sup": {
			"unreg_details": [],
			"comp_details": [],
			"uin_details": []
		},
		"itc_elg": {
			"itc_avl": [
			{
				"csamt": 0,
				"samt": 0,
				"ty": "IMPG",
				"camt": 0,
				"iamt": 0
			},
			{
				"csamt": 0,
				"samt": 0,
				"ty": "IMPS",
				"camt": 0,
				"iamt": 0
			},
			{
				"samt": 0,
				"csamt": 0,
				"ty": "ISRC",
				"camt": 0,
				"iamt": 0
			},
			{
				"ty": "ISD",
				"iamt": 1,
				"camt": 1,
				"samt": 1,
				"csamt": 1
			},
			{
				"samt": 0,
				"csamt": 0,
				"ty": "OTH",
				"camt": 0,
				"iamt": 0
			}
			],
			"itc_net": {
				"samt": 0,
				"csamt": 0,
				"camt": 0,
				"iamt": 0
			},
			"itc_inelg": [
			{
				"ty": "RUL",
				"iamt": 0,
				"camt": 0,
				"samt": 0,
				"csamt": 0
			},
			{
				"ty": "OTH",
				"iamt": 0,
				"camt": 0,
				"samt": 0,
				"csamt": 0
			}
		]
		}
	}

	gst_details = get_company_gst_details(address)

	report_dict["gstin"] = gst_details.get("gstin")

	account_heads = get_account_heads(company)

	outward_supply_tax_amounts = get_tax_amounts("Sales Invoice", "Regular")

	report_dict = prepare_data(report_dict, "sup_details", "osup_det", outward_supply_tax_amounts, account_heads)

	inward_supply_tax_amounts = get_tax_amounts("Purchase Invoice", "Regular", reverse_charge="Y")

	report_dict = prepare_data(report_dict, "sup_details", "isup_rev", inward_supply_tax_amounts, account_heads)

	return report_dict

def prepare_data(report_dict, supply_type, supply_category, tax_amounts, account_heads):

	tax_details = {}
	for d in tax_amounts:
		tax_details.setdefault(
			d.account_head,{
				"total_taxable": d.get("total"),
				"amount": d.get("tax_amount")
			}
		)

		report_dict['sup_details']['osup_det']['txval'] += d.tax_amount

	report_dict[supply_type][supply_category]['samt'] = flt(tax_details.get(account_heads.get("sgst_account"), {}).get("amount"))
	report_dict[supply_type][supply_category]['csamt'] = flt(tax_details.get(account_heads.get("cess_account"), {}).get("amount"))
	report_dict[supply_type][supply_category]['camt'] = flt(tax_details.get(account_heads.get("cgst_account"), {}).get("amount"))
	report_dict[supply_type][supply_category]['iamt'] = flt(tax_details.get(account_heads.get("igst_account"), {}).get("amount"))

	return report_dict

def get_tax_amounts(doctype, gst_category, reverse_charge="N"):

	return frappe.db.sql("""
		select sum(s.grand_total) as total, sum(t.tax_amount) as tax_amount, t.account_head
		from `tab{doctype}` s , `tabSales Taxes and Charges` t
		where t.parent = s.name and s.reverse_charge = %s
		group by t.account_head, s.invoice_type
		""".format(doctype=doctype), (reverse_charge), as_dict=1)

def get_company_gst_details(address):

	return frappe.db.get_all("Address",
		fields=["gstin", "gst_state", "gst_state_number"],
		filters={
			"name":address
		})[0]

def get_account_heads(company):

	return frappe.db.get_all("GST Account",
		fields=["cgst_account", "sgst_account", "igst_account", "cess_account"],
		filters={
			"company":company
		})[0]


@frappe.whitelist()
def view_report(company, address, month):
	report_dict = get_data(company, address, month)

	return frappe.render_template("erpnext/accounts/doctype/gstr_3b_report/gstr_3b_report.html", report_dict)


@frappe.whitelist()
def make_json(company, address, month):
	report_dict = get_data(company, address, month)

	json_data = frappe.as_json(report_dict)

	frappe.local.response.filename = "GST3B.json"
	frappe.local.response.filecontent = json_data
	frappe.local.response.type = "download"

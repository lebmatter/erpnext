# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json
from frappe.utils.file_manager import save_file

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
				"txval": 0
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
			}
		},
		"inter_sup": {
			"unreg_details": [
				{
					"pos": "26",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "01",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "17",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "34",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "30",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "18",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "20",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "22",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "04",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "08",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "03",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "24",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "36",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "23",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "32",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "09",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "06",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "19",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "07",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "05",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "29",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "37",
					"txval": 0,
					"iamt": 0
				},
				{
					"pos": "33",
					"txval": 0,
					"iamt": 0
				}
			]
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
			}
		}
	}

	gst_account_heads = frappe.db.get_all("GST Account",
		fields=["cgst_account", "sgst_account", "igst_account"],
		filters={
			"company":company
		})

	tax_details = frappe.db.sql("""
		select sum(s.grand_total), t.tax_amount
		from `tabSales Invoice` s , `tabSales Taxes and Charges` t
		where t.parent = s.name
		group by t.account_head """)

	gst_details = get_company_gst_details(address)

	report_dict["gstin"] = gst_details.get("gstin")

	return report_dict

def get_company_gst_details(address):

	return frappe.db.get_all("Address",
		fields=["gstin", "gst_state", "gst_state_number"],
		filters={
			"name":address
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

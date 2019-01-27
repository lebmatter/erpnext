# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
import json
from six import iteritems
from frappe.utils import flt, getdate

class GSTR3BReport(Document):
	def before_save(self):
		self.get_data()

	def get_data(self):
		self.report_dict = {
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
				},
				"osup_nongst": {
					"txval": 0,
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

		gst_details = get_company_gst_details(self.company_address)
		self.report_dict["gstin"] = gst_details.get("gstin")
		self.report_dict["ret_period"] = get_period(self.month, with_year=True)

		self.account_heads = get_account_heads(self.company)

		outward_supply_tax_amounts = get_tax_amounts("Sales Invoice", self.month)
		inward_supply_tax_amounts = get_tax_amounts("Purchase Invoice", self.month, reverse_charge="Y")
		itc_details = get_itc_details()

		self.prepare_data("Sales Invoice", outward_supply_tax_amounts, "sup_details", "osup_det", "Registered Regular")
		self.prepare_data("Sales Invoice", outward_supply_tax_amounts, "sup_details", "osup_zero", "SEZ")
		self.prepare_data("Purchase Invoice", inward_supply_tax_amounts, "sup_details", "isup_rev", "Registered Regular")
		self.report_dict["sup_details"]["osup_nongst"]["txval"] = get_non_gst_supply_value()



		self.json_output = frappe.as_json(self.report_dict)

	def set_itc_details(self, itc_details):

		itc_type_map = {
			'IMPG': 'Import Of Capital Goods',
			'IMPS': 'Import Of Service',
			'ISD': 'Input Service Distributor',
			'OTH': 'Others'
		}

		for d in self.report_dict["itc_elg"]["itc_avl"]:
			d["iamt"] = itc_details.get(d["ty"]).get("iamt")
			d["camt"] = itc_details.get(d["ty"]).get("camt")
			d["samt"] = itc_details.get(d["ty"]).get("samt")
			d["csamt"] = itc_details.get(d["ty"]).get("csamt")



	def prepare_data(self, doctype, tax_details, supply_type, supply_category, gst_category):

		account_map = {
			'sgst_account': 'samt',
			'cess_account': 'csamt',
			'cgst_account': 'camt',
			'igst_account': 'iamt'
		}

		self.report_dict[supply_type][supply_category]['txval'] = flt(get_total_taxable_value(doctype, gst_category, self.month))

		for k, v in iteritems(account_map):
			if v in self.report_dict.get(supply_type).get(supply_category):
				self.report_dict[supply_type][supply_category][v] = \
					flt(tax_details.get((self.account_heads.get(k), gst_category), {}).get("amount"))

def get_total_taxable_value(doctype, gst_category, month):

	month_no = get_period(month)

	return frappe.db.sql("""
		select sum(grand_total) as total
		from `tab{doctype}`
		where docstatus = 1 and month(posting_date) = %s and gst_category = %s
		"""
		.format(doctype = doctype), (month_no, gst_category), as_dict=1)[0].total

def get_itc_details():

	itc_amount = frappe.get_all('Purchase Invoice',
		fields = ["sum(itc_integrated_tax) as itc_iamt",
			"sum(itc_central_tax) as itc_camt",
			"sum(itc_state_tax) as itc_samt",
			"sum(itc_cess_amount) as itc_csamt",
			"eligibility_for_itc"
		],
		filters = {
			"docstatus":1,
		},
		group_by = 'eligibility_for_itc')

	itc_details = {}

	for d in itc_amount:
		itc_details.setdefault(d.eligibility_for_itc,{
			"itc_iamt": d.itc_iamt,
			"itc_camt": d.itc_camt,
			"itc_samt": d.itc_samt,
			"itc_csamt": d.itc_csamt
		})

	return itc_details


def get_non_gst_supply_value():

	return frappe.db.sql("""
		select sum(base_amount) as total from
		`tabSales Invoice Item` i, `tabSales Invoice` s
		where
		s.docstatus = 1 and
		i.parent = s.name and
		i.item_tax_rate = {} and
		s.taxes_and_charges IS NULL""", as_dict=1)[0].total


def get_tax_amounts(doctype, month, reverse_charge="N"):

	month_no = get_period(month)

	tax_amounts = frappe.db.sql("""
		select s.gst_category, sum(t.tax_amount) as tax_amount, t.account_head
		from `tab{doctype}` s , `tabSales Taxes and Charges` t
		where s.docstatus = 1 and t.parent = s.name and s.reverse_charge = %s and month(s.posting_date) = %s
		group by t.account_head, s.gst_category
		""".format(doctype=doctype), (reverse_charge, month_no), as_dict=1)

	tax_details = {}

	for d in tax_amounts:
		tax_details.setdefault(
			(d.account_head,d.gst_category),{
				"amount": d.get("tax_amount")
			}
		)

	return tax_details

def get_period(month, with_year=False):

	month_no = {
		"January": 1,
		"February": 2,
		"March": 3,
		"April": 4,
		"May": 5,
		"June": 6,
		"July": 7,
		"August": 8,
		"September": 9,
		"October": 10,
		"November": 11,
		"December": 12
	}.get(month)

	if with_year:
		return str(month_no).zfill(2) + str(getdate().year)
	else:
		return month_no

def get_company_gst_details(address):

	return frappe.get_all("Address",
		fields=["gstin", "gst_state", "gst_state_number"],
		filters={
			"name":address
		})[0]

def get_account_heads(company):

	return frappe.get_all("GST Account",
		fields=["cgst_account", "sgst_account", "igst_account", "cess_account"],
		filters={
			"company":company
		})[0]


@frappe.whitelist()
def view_report(name):

	json_data = frappe.get_value("GSTR 3B Report", name, 'json_output')
	return json.loads(json_data)

@frappe.whitelist()
def make_json(name):

	json_data = frappe.get_value("GSTR 3B Report", name, 'json_output')
	file_name = "GST3B.json"
	frappe.local.response.filename = file_name
	frappe.local.response.filecontent = json_data
	frappe.local.response.type = "download"

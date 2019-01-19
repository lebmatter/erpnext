// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('GSTR 3B Report', {

	onload : function(frm){
		frm.disable_save();
		frm.trigger('set_view_button');
		frm.trigger('generate_json');
	},

	setup: function(frm){
		frm.set_query('company_address', function(doc) {
			if(!doc.company) {
				frappe.throw(__('Please set Company'));
			}

			return {
				query: 'frappe.contacts.doctype.address.address.address_query',
				filters: {
					link_doctype: 'Company',
					link_name: doc.company
				}
			};
		});
	},

	set_view_button : frm => {

		const button_wrapper = frm.fields_dict.view.$wrapper;

		var view_button = $('<div >\
			<button class="btn btn-primary btn-view-report col-md-1" >View</button>\
			</div>').appendTo(button_wrapper);


		view_button.find(".btn-view-report")
		.on("click",function() {

			frappe.call({
				"method" : "erpnext.accounts.doctype.gstr_3b_report.gstr_3b_report.view_report",
				"args" : {
					company : frm.doc.company,
					address : frm.doc.company_address,
					month : frm.doc.month,
				},
				"callback" : function(r){

					let data = r.message

					frappe.ui.get_print_settings(false, print_settings => {

						frappe.render_grid({
							template: 'gstr_3b_report',
							title: __(this.doctype),
							print_settings: print_settings,
							data: data,
							columns:[]
						});
					});
				}
			});
		});
	},

	generate_json : frm => {

		const button_wrapper = frm.fields_dict.gen_json.$wrapper;

		var print_button = $('<div>\
			<button class="btn btn-primary btn-gen-json" style="margin-left:10px" >Generate Json</button>\
			</div>').appendTo(button_wrapper);

		print_button.find(".btn-gen-json")
		.on("click",function() {

			var w = window.open(
						frappe.urllib.get_full_url(
							"/api/method/erpnext.accounts.doctype.gstr_3b_report.gstr_3b_report.make_json?"
							+"company="+encodeURIComponent(frm.doc.company)
							+"&address="+encodeURIComponent(frm.doc.company_address)
							+"&month="+encodeURIComponent(frm.doc.month)));

			if(!w) {
				frappe.msgprint(__("Please enable pop-ups")); return;
			}

		});
	}
});

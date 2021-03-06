# Copyright (C) 2018 - TODAY, Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    fsm_order_id = fields.Many2one('fsm.order', string='FSM Order')


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    fsm_order_id = fields.Many2one('fsm.order', string='FSM Order')

    @api.model
    def create(self, vals):
        order = self.env['fsm.order'].browse(vals.get('fsm_order_id'))
        if order:
            if order.location_id.analytic_account_id:
                vals['account_analytic_id'] = order.location_id.\
                    analytic_account_id.id
            else:
                raise ValidationError(_("No analytic account" +
                                      " set on the order's Location"))

        return super(AccountInvoiceLine, self).create(vals)

    @api.onchange('product_id', 'quantity')
    def onchange_product_id(self):
        for line in self:
            if line.fsm_order_id:
                partner = line.fsm_order_id.person_id and\
                    line.fsm_order_id.person_id.partner_id or False
                if not partner:
                    raise ValidationError(_("Please set field service person"))
                fpos = partner.property_account_position_id
                prices = partner.property_product_pricelist
                tmpl = line.product_id.product_tmpl_id
                if line.product_id:
                    accounts = tmpl.get_product_accounts()
                    cost = prices.get_product_price(product=line.product_id,
                                                    quantity=line.quantity,
                                                    partner=partner,
                                                    date=False,
                                                    uom_id=False)
                    line.price_unit = cost
                    line.account_id = accounts['expense']
                    line.invoice_line_tax_ids = fpos.\
                        map_tax(tmpl.supplier_taxes_id)
                    line.name = line.product_id.name

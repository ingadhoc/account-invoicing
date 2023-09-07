##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, fields, api
from odoo.tools.misc import formatLang

import logging

_logger = logging.getLogger(__name__)


class AccountTax(models.Model):

    _inherit = "account.tax" 
    
    
    @api.model
    def _prepare_tax_totals(self, base_lines, currency, tax_lines=None):
        totals = super()._prepare_tax_totals(base_lines, currency, tax_lines)
        ##recorrer totals y si comple on la condicion y esta en self.env._context.get('tax_total_origin')
        tax_total_origin = self.env.context.get('tax_total_origin')
        if tax_total_origin:
            for subtotals_order in totals['subtotals_order']:
                for subtotals_index in range(0,len(totals['groups_by_subtotal'][subtotals_order])):
                    id_fixed = all([x.amount_type == 'fixed' and x.type_tax_use == 'purchase' for x in  self.env['account.tax'].search([('tax_group_id' ,'=', totals['groups_by_subtotal'][subtotals_order][subtotals_index]['tax_group_id'])])])
                    exist = [x for x in tax_total_origin['groups_by_subtotal'][subtotals_order] if x['tax_group_id'] == totals['groups_by_subtotal'][subtotals_order][subtotals_index]['tax_group_id']]

                    if id_fixed and exist:
                        totals['groups_by_subtotal'][subtotals_order][subtotals_index] =  exist[0]


            subtotals = []
            amount_tax = 0
            for subtotal_title in totals['subtotals_order']:
                amount_total = totals['amount_untaxed'] + amount_tax
                subtotals.append({
                    'name': subtotal_title,
                    'amount': amount_total,
                    'formatted_amount': formatLang(self.env, amount_total, currency_obj=currency),
                })
                amount_tax += sum(x['tax_group_amount'] for x in totals['groups_by_subtotal'][subtotal_title])

            amount_total = totals['amount_untaxed'] + amount_tax

            totals['amount_tax'] = amount_tax
        return totals

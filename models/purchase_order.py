# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class PurchaseOrder(models.Model):
    """Class to add new field in purchase order"""
    _inherit = 'purchase.order'

    requisition_order = fields.Char(string='Store Order', readonly=True,
                                    help='Set a requisition Order')

    def action_open_requisition_order(self):
        """Open the Issue request this purchase order originated from"""
        self.ensure_one()
        issue = self.env['employee.purchase.requisition'].sudo().search(
            [('name', '=', self.requisition_order)], limit=1)
        if issue:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'employee.purchase.requisition',
                'res_id': issue.id,
                'view_mode': 'form',
                'target': 'current',
            }

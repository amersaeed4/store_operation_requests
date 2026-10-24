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


class Picking(models.Model):
    """Class to add new field in stock picking"""
    _inherit = 'stock.picking'

    requisition_order = fields.Char(string='Store Order', readonly=True,
                                    help='Requisition order sequence')

    def action_open_requisition_order(self):
        """Open the Issue or Return request this picking originated from"""
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
        return_request = self.env['employee.return.request'].sudo().search(
            [('name', '=', self.requisition_order)], limit=1)
        if return_request:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'employee.return.request',
                'res_id': return_request.id,
                'view_mode': 'form',
                'target': 'current',
            }

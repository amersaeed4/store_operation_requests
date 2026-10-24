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
from odoo import api, models


class StockMove(models.Model):
    """Class to propagate the store order reference and destination
    location onto receipts auto-generated when a purchase order created
    from an Issue Request is confirmed."""
    _inherit = 'stock.move'

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        requisitions = self.env['employee.purchase.requisition'].sudo()
        for move in moves:
            order = move.purchase_line_id.sudo().order_id
            if not order or not order.requisition_order or not move.picking_id:
                continue
            requisition = requisitions.search(
                [('name', '=', order.requisition_order)], limit=1)
            if not requisition or not requisition.destination_location_id:
                continue
            move.location_dest_id = requisition.destination_location_id.id
            picking = move.picking_id
            if not picking.requisition_order:
                picking.requisition_order = requisition.name
            if picking.location_dest_id != requisition.destination_location_id:
                picking.location_dest_id = requisition.destination_location_id.id
        return moves

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
from odoo import api, fields, models


class RequisitionOrder(models.Model):
    """Model to add Requisition order details"""
    _name = 'requisition.order'
    _description = 'Requisition order'

    requisition_product_id = fields.Many2one(
        comodel_name='employee.purchase.requisition',
        help='Requisition product.')
    state = fields.Selection(string='State',
                             related='requisition_product_id.state')
    requisition_type = fields.Selection(string='Requisition Type', selection=[
        ('purchase_order', 'Purchase Order'),
        ('internal_transfer', 'Internal Transfer'), ],
                                        help='Type of requisition',
                                        required=True, default='purchase_order')
    product_id = fields.Many2one(comodel_name='product.product', required=True,
                                 help='Product')
    description = fields.Text(string="Description", compute='_compute_description',
                              store=True, readonly=False, precompute=True,
                              help='Product description')
    note = fields.Text(string='Note', help='Additional note for this line, if required')
    quantity = fields.Integer(string='Quantity', help='Product quantity', default=1)
    uom = fields.Char(related='product_id.uom_id.name',
                      string='Unit of Measure', help='Product unit of measure')
    qty_on_hand = fields.Float(string='Quantity on Hand', readonly=True,
                               compute='_compute_stock_quantities',
                               help='Quantity of the product currently on hand')
    incoming_qty = fields.Float(string='Incoming', readonly=True,
                                compute='_compute_stock_quantities',
                                help='Quantity of the product incoming from confirmed purchase orders')
    qty_in_department = fields.Float(string='Quantity in Department', readonly=True,
                                     compute='_compute_stock_quantities',
                                     help="Quantity of the product currently available at the "
                                          "location associated with the employee's department")
    partner_id = fields.Many2one(comodel_name='res.partner', string='Vendor',
                                 help='Vendor for the requisition',
                                 readonly=False)

    @api.depends('product_id')
    def _compute_stock_quantities(self):
        """Compute product quantity on hand, incoming, and quantity at the
        employee's department location, bypassing stock access rights so
        requisition users without Inventory access can see them."""
        for option in self:
            product = option.product_id.sudo()
            option.qty_on_hand = product.qty_available
            option.incoming_qty = product.incoming_qty
            dept_location = option.requisition_product_id.employee_id.sudo(
                ).department_id.department_location_id
            option.qty_in_department = (
                product.with_context(location=dept_location.id).qty_available
                if dept_location else 0.0)

    @api.depends('product_id')
    def _compute_description(self):
        """Compute product description"""
        for option in self:
            if not option.product_id:
                continue
            product_lang = option.product_id.with_context(
                lang=self.requisition_product_id.employee_id.lang)
            option.description = product_lang.get_product_multiline_description_sale()

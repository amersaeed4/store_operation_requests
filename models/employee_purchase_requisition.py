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
from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError


class PurchaseRequisition(models.Model):
    """Class for adding fields and functions for the store operation request model."""
    _name = 'employee.purchase.requisition'
    _description = 'Issue Request'
    _inherit = "mail.thread", "mail.activity.mixin"

    name = fields.Char(string="Reference Number", readonly=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee',
                                  required=True, help='Select an employee')
    dept_id = fields.Many2one(comodel_name='hr.department', string='Department',
                              related='employee_id.department_id', store=True,
                              help='Select an department')
    user_id = fields.Many2one(comodel_name='res.users', string='Responsible',
                              required=True,
                              domain=lambda self: [('share', '=', False),
                                                   ('id', '!=', self.env.uid)],
                              help='Select a user who is responsible for requisition')
    requisition_date = fields.Date(string="Requisition Date",
                                   default=lambda self: fields.Date.today(),
                                   help='Date of requisition')
    receive_date = fields.Date(string="Received Date", readonly=True,
                               help='Received date')
    requisition_deadline = fields.Date(string="Requisition Deadline",
                                       help="End date of store operation request")
    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help='Select a company')
    requisition_order_ids = fields.One2many(comodel_name='requisition.order',
                                            inverse_name='requisition_product_id',
                                            required=True)
    confirm_id = fields.Many2one(comodel_name='res.users',
                                 string='Confirmed By',
                                 default=lambda self: self.env.uid,
                                 readonly=True,
                                 help='User who confirmed the requisition.')
    manager_id = fields.Many2one(comodel_name='res.users',
                                 string='Department Manager', readonly=True,
                                 help='Select a department manager')
    requisition_head_id = fields.Many2one(comodel_name='res.users',
                                          string='Approved By', readonly=True,
                                          help='User who approved the requisition.')
    rejected_user_id = fields.Many2one(comodel_name='res.users',
                                       string='Rejected By', readonly=True,
                                       help='User who rejected the requisition')
    confirmed_date = fields.Date(string='Confirmed Date', readonly=True,
                                 help='Date of requisition confirmation')
    department_approval_date = fields.Date(string='Department Approval Date',
                                           readonly=True,
                                           help='Department approval date')
    approval_date = fields.Date(string='Approved Date', readonly=True,
                                help='Requisition approval date')
    reject_date = fields.Date(string='Rejection Date', readonly=True,
                              help='Requisition rejected date')
    source_location_id = fields.Many2one(comodel_name='stock.location',
                                         string='Source Location',
                                         help='Source location of requisition.', readonly=True)
    destination_location_id = fields.Many2one(comodel_name='stock.location',
                                              string="Destination Location",
                                              help='Destination location of requisition.', readonly=True)
    delivery_type_id = fields.Many2one(comodel_name='stock.picking.type',
                                       string='Delivery To',
                                       help='Type of delivery.', readonly=True)
    internal_picking_id = fields.Many2one(comodel_name='stock.picking.type',
                                          string="Internal Picking", readonly=True)
    requisition_description = fields.Text(string="Reason For Requisition")
    purchase_count = fields.Integer(string='Purchase Count',
                                    help='Purchase count',
                                    compute='_compute_purchase_count')
    internal_transfer_count = fields.Integer(string='Internal Transfer count',
                                             help='Internal transfer count',
                                             compute='_compute_internal_transfer_count')
    receipt_count = fields.Integer(string='Receipt Count',
                                   help='Receipt count',
                                   compute='_compute_receipt_count')
    state = fields.Selection([('new', 'New'), ('waiting_department_approval',
                                               'Waiting Department Approval'),
                              ('waiting_head_approval',
                               'Waiting Head Approval'),
                              ('approved', 'Approved'),
                              ('purchase_order_created',
                               'Orders Created'),
                              ('received', 'Received'),
                              ('cancelled', 'Cancelled')], default='new',
                             copy=False, tracking=True)

    def _compute_internal_transfer_count(self):
        """Function to compute the transfer count.

        Filters by picking_type_id so a receipt auto-generated from the
        Purchase Order (also tagged with this requisition's reference by the
        stock.move hook) doesn't get miscounted as an internal transfer.
        """
        for rec in self:
            if not rec.id or rec.name == 'New':
                rec.internal_transfer_count = 0
            else:
                rec.internal_transfer_count = self.env['stock.picking'].sudo().search_count([
                    ('requisition_order', '=', rec.name),
                    ('picking_type_id', '=', rec.internal_picking_id.id),
                ])

    def _compute_receipt_count(self):
        """Function to compute the receipt count (goods received from a
        vendor against the Purchase Order created for this requisition)."""
        for rec in self:
            if not rec.id or rec.name == 'New':
                rec.receipt_count = 0
            else:
                rec.receipt_count = self.env['stock.picking'].sudo().search_count([
                    ('requisition_order', '=', rec.name),
                    ('picking_type_id', '=', rec.delivery_type_id.id),
                ])

    def _compute_purchase_count(self):
        """Function to compute the purchase count"""
        for rec in self:
            if not rec.id or rec.name == 'New':
                rec.purchase_count = 0
            else:
                rec.purchase_count = self.env['purchase.order'].sudo().search_count([
                    ('requisition_order', '=', rec.name)
                ])

    def unlink(self):
        for rec in self:
            for po in self.env['purchase.order'].search([('requisition_order', '=', rec.name)]):
                if po.state == 'purchase':
                     raise UserError("You cannot delete this record as the purchase order is confirmed")
                else:
                    po.write({'state':'cancel'})
        return super().unlink()


    @api.model_create_multi
    def create(self, vals_list):
        """Function to generate store operation request sequence"""
        for vals in vals_list:
            name = vals.get('name')
            if not name or name == _('New') or self.search([('name', '=', name)], limit=1):
                vals['name'] = self.env['ir.sequence'].next_by_code('employee.purchase.requisition') or _('New')
        return super().create(vals_list)

    def _notify_group(self, group_xmlid, summary, note, due_date):
        """Post an inbox notification and schedule a To-Do activity, due on
        the given date, for every user in the given group (including via
        implied/inherited group membership)."""
        self.ensure_one()
        group = self.env.ref(group_xmlid, raise_if_not_found=False)
        users = group.all_user_ids.filtered(lambda u: not u.share) if group else self.env['res.users']
        if not users:
            return
        self.message_post(body=note, partner_ids=users.partner_id.ids)
        for user in users:
            self.activity_schedule(
                act_type_xmlid='mail.mail_activity_data_todo',
                date_deadline=due_date,
                summary=summary,
                note=note,
                user_id=user.id,
            )

    def action_confirm_requisition(self):
        """Function to confirm store operation request"""
        if not self.requisition_order_ids:
            raise UserError("Add at least a requisition order before confirming.")
        default_location = self.env.ref('stock.stock_location_stock')
        self.source_location_id = default_location.id
        self.destination_location_id = (
            self.employee_id.sudo().employee_location_id.id) if (
            self.employee_id.sudo().employee_location_id) else (
            self.employee_id.sudo().department_id.department_location_id.id) if (
            self.employee_id.sudo().department_id.department_location_id) else (
            default_location.id)
        self.delivery_type_id = (
            self.source_location_id.warehouse_id.in_type_id.id)
        self.internal_picking_id = (
            self.source_location_id.warehouse_id.int_type_id.id)
        self.write({'state': 'waiting_department_approval'})
        self.confirm_id = self.env.uid
        self.confirmed_date = fields.Date.today()
        self._notify_group(
            'store_operation_requests.employee_requisition_head',
            _('New Issue Request: %s', self.name),
            _('%(employee)s submitted a new Issue Request that needs department approval.',
              employee=self.employee_id.sudo().name),
            self.requisition_deadline or fields.Date.today(),
        )

    def action_department_approval(self):
        """Approval from department"""
        self.write({'state': 'waiting_head_approval'})
        self.manager_id = self.env.uid
        self.department_approval_date = fields.Date.today()
        self._notify_group(
            'store_operation_requests.employee_requisition_manager',
            _('Issue Request awaiting final approval: %s', self.name),
            _('%(employee)s\'s Issue Request has been approved by the department and needs your final approval.',
              employee=self.employee_id.sudo().name),
            self.requisition_deadline or fields.Date.today(),
        )

    def action_department_cancel(self):
        """Cancellation from department """
        self.write({'state': 'cancelled'})
        self.rejected_user_id = self.env.uid
        self.reject_date = fields.Date.today()

    def action_head_approval(self):
        """Final approval from the requisition manager"""
        self.write({'state': 'approved'})
        self.requisition_head_id = self.env.uid
        self.approval_date = fields.Date.today()
        self._notify_group(
            'purchase.group_purchase_manager',
            _('Issue Request ready for purchasing: %s', self.name),
            _('%(employee)s\'s Issue Request has been fully approved and is ready to generate a Purchase Order/transfer.',
              employee=self.employee_id.sudo().name),
            self.requisition_deadline or fields.Date.today(),
        )

    def action_head_cancel(self):
        """Cancellation from department head"""
        self.write({'state': 'cancelled'})
        self.rejected_user_id = self.env.uid
        self.reject_date = fields.Date.today()

    def _get_fallback_vendor(self):
        """Get-or-create the placeholder vendor used when no vendor was
        selected on a requisition line. Vendor selection is the Purchase
        Department's job, done later on the resulting draft order."""
        Partner = self.env['res.partner'].sudo()
        vendor = Partner.search([('name', '=', 'Vendor To Be Determined')], limit=1)
        if not vendor:
            vendor = Partner.create({
                'name': 'Vendor To Be Determined',
                'is_company': True,
                'supplier_rank': 1,
                'comment': ('Placeholder vendor auto-assigned by Store Operation '
                            'Requests when no vendor was selected. Replace with the '
                            'actual vendor before confirming this order.'),
            })
        return vendor

    def action_create_purchase_order(self):
        """Create purchase order and internal transfer.

        Vendor selection is the Purchase Department's job, not this app's -
        lines never carry a vendor at this point, so a fallback (the
        product's preferred vendor, or a placeholder) is used to satisfy
        the mandatory field on purchase.order. Procurement corrects it
        on the resulting draft order.
        """
        PurchaseOrder = self.env['purchase.order'].sudo()
        fallback_vendor = self._get_fallback_vendor()
        vendor_po_map = {}
        for rec in self.requisition_order_ids:
            if rec.requisition_type == 'internal_transfer':
                self.env['stock.picking'].sudo().create({
                    'location_id': self.source_location_id.id,
                    'location_dest_id': self.destination_location_id.id,
                    'picking_type_id': self.internal_picking_id.id,
                    'requisition_order': self.name,
                    'move_ids': [Command.create({
                        'product_id': rec.product_id.id,
                        'product_uom': rec.product_id.uom_id.id,
                        'product_uom_qty': rec.quantity,
                        'location_id': self.source_location_id.id,
                        'location_dest_id': self.destination_location_id.id,
                    })]
                })
            else:
                vendor = (rec.partner_id or rec.product_id.seller_ids[:1].partner_id
                          or fallback_vendor).id
                if vendor in vendor_po_map:
                    po = vendor_po_map[vendor]
                else:
                    po = PurchaseOrder.create({
                        'partner_id': vendor,
                        'requisition_order': self.name,
                    })
                    vendor_po_map[vendor] = po
                po.write({
                    "order_line": [Command.create({
                        'product_id': rec.product_id.id,
                        'product_qty': rec.quantity,
                    })]
                })
        self.write({'state': 'purchase_order_created'})

    def action_receive(self):
        """Received store operation request"""
        self.write({'state': 'received'})
        self.receive_date = fields.Date.today()

    def get_purchase_order(self):
        """Purchase order smart button view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Order',
            'view_mode': 'list,form',
            'res_model': 'purchase.order',
            'domain': [('requisition_order', '=', self.name)],
        }

    def get_internal_transfer(self):
        """Internal transfer smart tab view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Internal Transfers',
            'view_mode': 'list,form',
            'res_model': 'stock.picking',
            'domain': [('requisition_order', '=', self.name),
                       ('picking_type_id', '=', self.internal_picking_id.id)],
        }

    def get_receipt(self):
        """Receipt smart tab view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Receipts',
            'view_mode': 'list,form',
            'res_model': 'stock.picking',
            'domain': [('requisition_order', '=', self.name),
                       ('picking_type_id', '=', self.delivery_type_id.id)],
        }

    def action_print_report(self):
        """Print store operation request report.

        No custom `data` is passed: keeping it empty lets the web client embed
        the record id(s) directly in the download URL, which is required for
        Odoo to honour the report's `print_report_name` (otherwise it silently
        falls back to a fixed generic filename).
        """
        return self.env.ref(
            'store_operation_requests.'
            'action_report_purchase_requisition').report_action(self)

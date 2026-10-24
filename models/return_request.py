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


class ReturnRequest(models.Model):
    """Class for adding fields and functions for the return request model."""
    _name = 'employee.return.request'
    _description = 'Return Request'
    _inherit = "mail.thread", "mail.activity.mixin"

    name = fields.Char(string="Reference No", readonly=True)
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee',
                                  required=True, help='Select an employee')
    dept_id = fields.Many2one(comodel_name='hr.department', string='Department',
                              related='employee_id.department_id', store=True,
                              help='Select an department')
    user_id = fields.Many2one(comodel_name='res.users', string='Responsible',
                              required=True,
                              domain=lambda self: [('share', '=', False),
                                                   ('id', '!=', self.env.uid)],
                              help='Select a user who is responsible for the return')
    requisition_date = fields.Date(string="Return Date",
                                   default=lambda self: fields.Date.today(),
                                   help='Date of return request')
    receive_date = fields.Date(string="Received Date", readonly=True,
                               help='Date the store received the returned items')
    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help='Select a company')
    return_order_ids = fields.One2many(comodel_name='return.request.line',
                                       inverse_name='return_request_id',
                                       required=True)
    confirm_id = fields.Many2one(comodel_name='res.users', string='Confirmed By',
                                 default=lambda self: self.env.uid, readonly=True,
                                 help='User who confirmed the return request.')
    manager_id = fields.Many2one(comodel_name='res.users',
                                 string='Department Manager', readonly=True,
                                 help='Select a department manager')
    requisition_head_id = fields.Many2one(comodel_name='res.users',
                                          string='Approved By', readonly=True,
                                          help='User who approved the return request.')
    rejected_user_id = fields.Many2one(comodel_name='res.users',
                                       string='Rejected By', readonly=True,
                                       help='User who rejected the return request')
    confirmed_date = fields.Date(string='Confirmed Date', readonly=True,
                                 help='Date of return confirmation')
    department_approval_date = fields.Date(string='Department Approval Date',
                                           readonly=True,
                                           help='Department approval date')
    approval_date = fields.Date(string='Approved Date', readonly=True,
                                help='Return request approval date')
    reject_date = fields.Date(string='Rejection Date', readonly=True,
                              help='Return request rejected date')
    source_location_id = fields.Many2one(comodel_name='stock.location',
                                         string='Source Location',
                                         help='Location the returned items are coming from.',
                                         readonly=True)
    destination_location_id = fields.Many2one(comodel_name='stock.location',
                                              string="Destination Location",
                                              help='Location the returned items are going to.',
                                              readonly=True)
    internal_picking_id = fields.Many2one(comodel_name='stock.picking.type',
                                          string="Internal Picking", readonly=True)
    requisition_description = fields.Text(string="Reason For Return")
    internal_transfer_count = fields.Integer(string='Internal Transfer count',
                                             help='Internal transfer count',
                                             compute='_compute_internal_transfer_count')
    state = fields.Selection([('new', 'New'), ('waiting_department_approval',
                                               'Waiting Department Approval'),
                              ('waiting_head_approval',
                               'Waiting Head Approval'),
                              ('approved', 'Approved'),
                              ('transfer_created', 'Transfer Created'),
                              ('received', 'Received'),
                              ('cancelled', 'Cancelled')], default='new',
                             copy=False, tracking=True)

    def _compute_internal_transfer_count(self):
        """Function to compute the transfer count"""
        for rec in self:
            if not rec.id or rec.name == 'New':
                rec.internal_transfer_count = 0
            else:
                rec.internal_transfer_count = self.env['stock.picking'].sudo().search_count([
                    ('requisition_order', '=', rec.name)
                ])

    def unlink(self):
        for rec in self:
            for picking in self.env['stock.picking'].sudo().search(
                    [('requisition_order', '=', rec.name)]):
                if picking.state == 'done':
                    raise UserError(
                        "You cannot delete this record as the transfer is completed")
                else:
                    picking.write({'state': 'cancel'})
        return super().unlink()

    @api.model_create_multi
    def create(self, vals_list):
        """Function to generate return request sequence"""
        for vals in vals_list:
            name = vals.get('name')
            if not name or name == _('New') or self.search([('name', '=', name)], limit=1):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'employee.return.request') or _('New')
        return super().create(vals_list)

    def action_confirm_return(self):
        """Function to confirm return request"""
        if not self.return_order_ids:
            raise UserError("Add at least a return line before confirming.")
        default_location = self.env.ref('stock.stock_location_stock')
        self.destination_location_id = default_location.id
        self.source_location_id = (
            self.employee_id.sudo().employee_location_id.id) if (
            self.employee_id.sudo().employee_location_id) else (
            self.employee_id.sudo().department_id.department_location_id.id) if (
            self.employee_id.sudo().department_id.department_location_id) else (
            default_location.id)
        self.internal_picking_id = (
            self.destination_location_id.warehouse_id.int_type_id.id)
        self.write({'state': 'waiting_department_approval'})
        self.confirm_id = self.env.uid
        self.confirmed_date = fields.Date.today()
        self._notify_group(
            'store_operation_requests.employee_requisition_head',
            _('New Return Request: %s', self.name),
            _('%(employee)s submitted a new Return Request that needs department approval.',
              employee=self.employee_id.sudo().name),
            fields.Date.today(),
        )

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

    def action_department_approval(self):
        """Approval from department"""
        self.write({'state': 'waiting_head_approval'})
        self.manager_id = self.env.uid
        self.department_approval_date = fields.Date.today()
        self._notify_group(
            'store_operation_requests.employee_requisition_manager',
            _('Return Request awaiting final approval: %s', self.name),
            _('%(employee)s\'s Return Request has been approved by the department and needs your final approval.',
              employee=self.employee_id.sudo().name),
            fields.Date.today(),
        )

    def action_department_cancel(self):
        """Cancellation from department"""
        self.write({'state': 'cancelled'})
        self.rejected_user_id = self.env.uid
        self.reject_date = fields.Date.today()

    def action_head_approval(self):
        """Final approval from the requisition manager"""
        self.write({'state': 'approved'})
        self.requisition_head_id = self.env.uid
        self.approval_date = fields.Date.today()
        self._notify_group(
            'stock.group_stock_manager',
            _('Return Request ready for transfer: %s', self.name),
            _('%(employee)s\'s Return Request has been fully approved and is ready for the internal transfer to be created.',
              employee=self.employee_id.sudo().name),
            fields.Date.today(),
        )

    def action_head_cancel(self):
        """Cancellation from department head"""
        self.write({'state': 'cancelled'})
        self.rejected_user_id = self.env.uid
        self.reject_date = fields.Date.today()

    def action_create_transfer(self):
        """Create the internal transfer sending returned items back to the store"""
        self.env['stock.picking'].sudo().create({
            'location_id': self.source_location_id.id,
            'location_dest_id': self.destination_location_id.id,
            'picking_type_id': self.internal_picking_id.id,
            'requisition_order': self.name,
            'move_ids': [Command.create({
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty': line.quantity,
                'location_id': self.source_location_id.id,
                'location_dest_id': self.destination_location_id.id,
            }) for line in self.return_order_ids]
        })
        self.write({'state': 'transfer_created'})

    def action_receive(self):
        """Received return request"""
        self.write({'state': 'received'})
        self.receive_date = fields.Date.today()

    def get_internal_transfer(self):
        """Internal transfer smart tab view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Internal Transfers',
            'view_mode': 'list,form',
            'res_model': 'stock.picking',
            'domain': [('requisition_order', '=', self.name)],
        }

    def action_print_report(self):
        """Print return request report.

        No custom `data` is passed: keeping it empty lets the web client embed
        the record id(s) directly in the download URL, which is required for
        Odoo to honour the report's `print_report_name` (otherwise it silently
        falls back to a fixed generic filename).
        """
        return self.env.ref(
            'store_operation_requests.'
            'action_report_return_request').report_action(self)

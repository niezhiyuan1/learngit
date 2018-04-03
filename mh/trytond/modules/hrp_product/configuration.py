from trytond.model import fields
from trytond.pyson import Eval, Bool
from trytond.pool import PoolMeta

DATE_STATE = [
    ('none', 'None'),
    ('optional', 'Optional'),
    ('required', 'Required'),
    ]

class Configuration:
    "Configuration"
    __metaclass__ = PoolMeta
    __name__ = 'product.configuration'

    account_payable = fields.Property(fields.Many2One('account.account',
            'Account Payable', domain=[
                ('kind', '=', 'payable'),
                ('company', '=', Eval('context', {}).get('company', -1)),
                ],
            states={
                'required': Bool(Eval('context', {}).get('company')),
                'invisible': ~Eval('context', {}).get('company'),
                }))
    account_receivable = fields.Property(fields.Many2One('account.account',
            'Account Receivable', domain=[
                ('kind', '=', 'receivable'),
                ('company', '=', Eval('context', {}).get('company', -1)),
                ],
            states={
                'required': Bool(Eval('context', {}).get('company')),
                'invisible': ~Eval('context', {}).get('company'),
                }))
    account_revenue = fields.Property(fields.Many2One('account.account',
            'Account Revenue', domain=[
                ('kind', '=', 'revenue'),
                ('company', '=', Eval('context', {}).get('company', -1)),
                ], required=True))
    account_expense = fields.Property(fields.Many2One('account.account',
            'Account Expense', domain=[
                ('kind', '=', 'expense'),
                ('company', '=', Eval('context', {}).get('company', -1)),
                ], required=True),)
    shelf_life_state = fields.Selection(
        DATE_STATE, 'Shelf Life Time State', sort=False)
    expiration_state = fields.Selection(
        DATE_STATE, 'Expiration State', sort=False)

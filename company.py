# -*- coding: utf-8 -*-
"""
    company

    Configuration of Avatax settings with the company

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import fields, ModelView
from trytond.pool import PoolMeta
from trytond.pyson import Eval, Bool
from trytond.rpc import RPC

import avatax
from avatax.api import PRODUCTION_URL

__all__ = ['Company']
__metaclass__ = PoolMeta

REQUIRED_FOR_AVATAX = {
    'required': Bool(Eval('enable_avatax'))
}


class Company:
    "Company"
    __name__ = 'company.company'

    enable_avatax = fields.Boolean('Enable Avatax')
    avatax_account_number = fields.Char(
        'Account Number', states=REQUIRED_FOR_AVATAX,
        depends=['enable_avatax']
    )
    avatax_license_key = fields.Char(
        'License Key', states=REQUIRED_FOR_AVATAX,
        depends=['enable_avatax']
    )
    avatax_url = fields.Char(
        'URL', states=REQUIRED_FOR_AVATAX,
        depends=['enable_avatax']
    )
    avatax_company_code = fields.Char(
        'Company Code', states=REQUIRED_FOR_AVATAX,
        depends=['enable_avatax']
    )
    avatax_disable_tax_calculation = fields.Boolean('Disable Tax Calculation')
    avatax_disable_address_validation = fields.Boolean(
        'Disable Address Validation'
    )
    avatax_enable_logging = fields.Boolean('Enable Avatax Logging')
    avatax_request_timeout = fields.Integer('Request Timeout')
    avatax_uppercase_addresses = fields.Boolean(
        'Upper Case Addresses', states={
            'invisible': Bool(Eval('avatax_disable_address_validation'))
        }, depends=['avatax_disable_address_validation']
    )

    default_tax_credit_note_account = fields.Many2One(
        'account.account', 'Default Tax Credit Account',
        domain=[
            ('company', '=', Eval('company')),
            ('kind', 'not in', ['view', 'receivable', 'payable']),
        ],
        states=REQUIRED_FOR_AVATAX, depends=['company', 'type']
    )
    default_tax_invoice_account = fields.Many2One(
        'account.account', 'Default Invoice Account',
        domain=[
            ('company', '=', Eval('company')),
            ('kind', 'not in', ['view', 'receivable', 'payable']),
        ],
        states=REQUIRED_FOR_AVATAX, depends=['company', 'type']
    )

    @staticmethod
    def default_avatax_request_timeout():
        return 300

    @staticmethod
    def default_avatax_url():
        return PRODUCTION_URL

    @staticmethod
    def default_enable_avatax():
        return False

    @classmethod
    @ModelView.button
    def test_avatax_connection(cls, companies):
        if not len(companies) == 1:
            cls.raise_user_error('test_many_companies')
        company, = companies
        api_client = company.avatax_api()
        api_client.test_connection()

    def avatax_api(self):
        """
        Return the Avatax API client for the current company
        """
        if not self.enable_avatax:
            self.raise_user_error('avatax_not_enabled')
        return avatax.API(
            self.avatax_account_number, self.avatax_license_key, self.avatax_url
        )

    @classmethod
    def __setup__(cls):
        super(Company, cls).__setup__()
        cls.__rpc__.update({
            'test_avatax_connection': RPC(True, 0)
        })
        cls._error_messages.update({
            'avatax_not_enabled': 'Avatax is not enabled for your '
                                  'current company',
            'test_many_companies': 'Test Connection needs to be done'
                                   ' separately for each company',
        })

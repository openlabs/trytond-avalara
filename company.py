# -*- coding: utf-8 -*-
"""
    company

    Configuration of Avatax settings with the company

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Company']

__metaclass__ = PoolMeta

class Company:
    "Company"
    __name__ = 'company.company'

    license_key = fields.Char('License Key', required=True)
    url = fields.Char('URL', required=True)
    company_code = fields.Char('Company Code', required=True)
    disable_tax_calculation = fields.Boolean('Disable Tax Calculation')
    disable_address_validation = fields.Boolean('Disable Address Validation')
    #address validation countries
    enable_avatax_logging = fields.Boolean('Enable Avatax Logging')
    request_timeout = fields.Integer('Request Timeout')
    uppercase_addresses = fields.Boolean('Upper Case Addresses')

    @staticmethod
    def default_request_timeout():
        return 300

# -*- coding: utf-8 -*-
"""
    account

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from decimal import Decimal

from trytond.model import fields
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction

__all__ = ['Tax']
__metaclass__ = PoolMeta


class Tax:
    "Taxes"
    __name__ = 'account.tax'

    juris_type = fields.Selection([
        ('State', 'State'),
        ('County', 'County'),
        ('Other', 'Other')
    ], 'Jurisdiction Type')
    juris_name = fields.Char('Jurisdiction Name')

    @classmethod
    def get_matching_tax(cls, avatax_line):
        """
        Find a matching tax line, or create one and send back

        :param avatax_line: The line as returned by the Avatax API
                            {
                                u'Country': u'US',
                                u'JurisName': u'FLORIDA',
                                u'JurisType': u'State',
                                u'Rate': u'0.060000',
                                u'Region': u'FL',
                                u'Tax': u'60',
                                u'TaxName': u'FL STATE TAX',
                                u'Taxable': u'1000'
                            }
        """
        Company = Pool().get('company.company')

        company = Company(Transaction().context['company'])

        try:
            tax, = cls.search([
                ('juris_name', '=', avatax_line['JurisName']),
                ('juris_type', '=', avatax_line['JurisType']),
                ('name', '=', avatax_line['TaxName']),
                ('percentage', '=', Decimal(avatax_line['Rate']) * 100)
            ])
        except ValueError:
            data = {
                'name': avatax_line['TaxName'],
                'percentage': Decimal(avatax_line['Rate']) * 100,
                'juris_name': avatax_line['JurisName'],
                'juris_type': avatax_line['JurisType'],
                'description': '%s (%s/%s)' % (
                    avatax_line['TaxName'],
                    avatax_line['Country'],
                    avatax_line['Region'],
                )
            }
            data['invoice_account'] = company.default_tax_invoice_account
            data['credit_note_account'] = company.default_tax_credit_note_account
            tax = cls.create(data)
        return tax

# -*- coding: utf-8 -*-
"""
    account

    :copyright: © 2013-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from decimal import Decimal

from trytond.model import fields
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval
from trytond.transaction import Transaction

__all__ = ['Tax', 'TaxCode']
__metaclass__ = PoolMeta

STATES = {
    'readonly': ~Eval('active'),
}
DEPENDS = ['active']


class Tax:
    "Taxes"
    __name__ = 'account.tax'

    avatax_name = fields.Char('Avatax Name', readonly=True)

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
        TaxCode = Pool().get('account.tax.code')

        company = Company(Transaction().context['company'])

        with Transaction().set_user(0):
            tax_base_code = TaxCode.get_or_create_from(
                avatax_line, is_base=True)
            tax_code = TaxCode.get_or_create_from(
                avatax_line, is_base=False)

            try:
                tax, = cls.search([
                    ('invoice_base_code', '=', tax_base_code),
                    ('invoice_tax_code', '=', tax_code),
                    ('avatax_name', '=', avatax_line['TaxName']),
                    ('rate', '=', Decimal(avatax_line['Rate']))
                ])
            except ValueError:
                tax, = cls.create([{
                    'name': avatax_line['TaxName'],
                    'avatax_name': avatax_line['TaxName'],
                    'description': '%s (%s/%s)' % (
                        avatax_line['TaxName'],
                        avatax_line['Country'],
                        avatax_line['Region'],
                    ),

                    # Rate
                    'rate': Decimal(avatax_line['Rate']),

                    # Tax codes
                    'invoice_tax_code': tax_code,
                    'credit_note_tax_code': tax_code,
                    'invoice_base_code': tax_base_code,
                    'credit_note_base_code': tax_base_code,

                    # Tax code signs.
                    # Credit notes mean reversal
                    'invoice_tax_sign': 1,
                    'invoice_base_sign': 1,
                    'credit_note_tax_sign': -1,
                    'credit_note_base_sign': -1,

                    # Tax accounts. The GL to which tax has to be accounted.
                    'invoice_account': company.default_tax_invoice_account,
                    'credit_note_account': (
                        company.default_tax_credit_note_account),
                }])
        return tax


class TaxCode:
    """
    Tax Code

    A tax code is created for each Tax Jurisdiction where a return will have
    to be filed.
    """
    __name__ = 'account.tax.code'

    country = fields.Many2One(
        'country.country', 'Country',
        states=STATES, depends=DEPENDS
    )
    subdivision = fields.Many2One("country.subdivision",
            'Subdivision', domain=[('country', '=', Eval('country'))],
            states=STATES, depends=['active', 'country'])

    # XXX: This could be a Select field if all values are known
    juris_type = fields.Char('Jurisdiction Type', states=STATES)
    juris_name = fields.Char('Jurisdiction Name', states=STATES)

    is_base = fields.Boolean(
        'Is Base',
        help="Indicates if the code is used to represent the sales value or Tax"
    )
    is_region = fields.Boolean(
        'Is Region',
        help="A tax code for a region (like state, province)"
    )

    @fields.depends('country', 'subdivision')
    def on_change_country(self):
        if (self.subdivision
                and self.subdivision.country != self.country):
            return {'subdivision': None}
        return {}

    @classmethod
    def make_name_from(cls, avatax_detail, is_base):
        """
        Return a string that can be used as name for the given avatax
        detail
        """
        name = avatax_detail['TaxName']

        if avatax_detail['JurisType'] != 'State':
            name += u' [%s]' % avatax_detail['JurisName']

        if is_base:
            # This is a code for base value. So indicate in code that the
            # sum indicates the base and not the tax
            name = 'Sales: ' + name
        else:
            # A visual clue in the name to indicate that the tax code
            # indicates the Tax (not assessable value)
            name = 'Tax: ' + name

        return name

    @classmethod
    def get_or_create_from(cls, avatax_detail, is_base):
        """
        Checks if an existing tax code exists which matches the tax spec.
        If there is one, it is returned. Else return after creating a new one.

        :param avatax_detail: Details of a tax sent by Avalara
        :param is_base: If true returns the code designated for base codes.
        """
        Country = Pool().get('country.country')
        Subdivision = Pool().get('country.subdivision')

        subdivision_code = '-'.join([
            avatax_detail['Country'], avatax_detail['Region']
        ])
        try:
            tax_code, = cls.search([
                ('country.code', '=', avatax_detail['Country']),
                ('subdivision.code', '=', subdivision_code),
                ('juris_type', '=', avatax_detail['JurisType']),
                ('juris_name', '=', avatax_detail['JurisName']),
                ('is_base', '=', is_base),
            ])
        except ValueError:
            country, = Country.search(
                [('code', '=', avatax_detail['Country'])]
            )
            subdivision, = Subdivision.search([('code', '=', subdivision_code)])
            tax_code, = cls.create([{
                'name': cls.make_name_from(avatax_detail, is_base),
                'country': country,
                'subdivision': subdivision,
                'juris_type': avatax_detail['JurisType'],
                'juris_name': avatax_detail['JurisName'],
                'is_base': is_base,
                'parent': cls.get_or_create_region_tax_code(
                    subdivision
                )
            }])
        return tax_code

    @classmethod
    def get_or_create_region_tax_code(cls, subdivision):
        """
        :param subdivision: The AR of subdivision for which the region
                            has to be returned.
        """
        try:
            tax_code, = cls.search([
                ('subdivision', '=', subdivision),
                ('is_region', '=', True)
            ])
        except ValueError:
            tax_code, = cls.create([{
                'name': subdivision.code,
                'is_region': True,
                'subdivision': subdivision,
                'country': subdivision.country,
            }])
        return tax_code

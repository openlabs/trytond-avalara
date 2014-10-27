# -*- coding: utf-8 -*-
"""
    party

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import fields, ModelView, ModelSQL
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction
from trytond.rpc import RPC
from .company import wrap_avatax_error

__all__ = ['Party', 'CustomerUsageType', 'Address']

__metaclass__ = PoolMeta


class CustomerUsageType(ModelSQL, ModelView):
    "Customer Usage Type"
    __name__ = 'avatax.customer_usage_type'

    code = fields.Char('Code', required=True)
    name = fields.Char('Name', required=True)


class Party:
    "Party"
    __name__ = 'party.party'

    tax_exemption_number = fields.Char("Tax Exemption Number")
    auto_update_avatax = fields.Boolean('Auto Update Avatax')
    customer_usage_type = fields.Many2One(
        'avatax.customer_usage_type', 'Customer Usage Type'
    )


class Address:
    "Address"
    __name__ = "party.address"

    @classmethod
    def __setup__(cls):
        super(Address, cls).__setup__()
        cls.__rpc__.update({
            'validate_address_avatax': RPC(False, 0)
        })
        cls._error_messages.update({
            'address_validation_disabled': 'Address Validation is disabled for'
                                           ' the current company'
        })

    def _as_avatax_address(self):
        """
        Returns a JSON serializable dictionary of the address
        """
        return dict(
            Line1=self.street,
            Line2=self.streetbis,
            City=self.city,
            Region=self.subdivision and self.subdivision.name or '',
            Country=self.country and self.country.name or '',
            PostalCode=self.zip
        )

    @wrap_avatax_error
    def _validate_address_avatax(self):
        """
        Validate the current address with Avatax and save the
        response as the address
        """
        Company = Pool().get('company.company')
        Country = Pool().get('country.country')
        Subdivision = Pool().get('country.subdivision')

        company = Company(Transaction().context['company'])
        if company.avatax_disable_address_validation:
            self.raise_user_error('address_validation_disabled')

        # TODO: Validate if the address is in one of the countries avatax
        # is enabled for
        validated_address = company.avatax_api().address_validate(
            **self._as_avatax_address()
        )
        values = {
            'street': validated_address.get('Line1'),
            'streetbis': ', '.join(
                filter(
                    None, [
                        validated_address.get('Line2'),
                        validated_address.get('Line3'),
                    ]
                )
            ),
            'city': validated_address.get('City'),
            'zip': validated_address.get('PostalCode'),
        }

        if 'Country' in validated_address:
            values['country'], = Country.search([
                ('code', '=', validated_address['Country'])
            ])

        if 'Region' in validated_address and 'country' in values:
            subdivision_code = '-'.join([
                values['country'].code, validated_address['Region']
            ])
            values['subdivision'], = Subdivision.search([
                ('code', '=', subdivision_code)
            ])

        self.write([self], values)

    @classmethod
    @ModelView.button
    def validate_address_avatax(cls, addresses):
        """
        Validate the addresses
        """
        for address in addresses:
            address._validate_address_avatax()

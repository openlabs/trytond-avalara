# -*- coding: utf-8 -*-
"""
    sale


    :copyright: © 2013-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from decimal import Decimal
from datetime import datetime

from trytond.pool import PoolMeta, Pool
from trytond.model import ModelView, Workflow, fields

from .company import wrap_avatax_error

__all__ = ['Sale', 'SaleLine']
__metaclass__ = PoolMeta


class Sale:
    "Sale"
    __name__ = "sale.sale"

    tax_update_date = fields.DateTime('Tax Details Update Time', readonly=True)

    def _get_avatax_data(self):
        """
        Returns the data dictionary that is used by the `get_taxes_from_avatax`
        method.

        This is separated to make it easier for downstream module to modify
        the values easily.
        """
        addresses = []

        if self.invoice_address:
            invoice_address = self.invoice_address._as_avatax_address()
            invoice_address['AddressCode'] = self.invoice_address.id
            addresses.append(invoice_address)

        shipment_address = self.shipment_address._as_avatax_address()
        shipment_address['AddressCode'] = self.shipment_address.id
        addresses.append(shipment_address)

        warehouse_address = self.warehouse.address._as_avatax_address()
        warehouse_address['AddressCode'] = self.warehouse.address.id
        addresses.append(warehouse_address)

        return {
            u'DocDate': self.sale_date.strftime("%Y-%m-%d"),
            u'CustomerCode': self.party.code,
            u'CurrencyCode': self.currency.code,
            u'Lines': filter(
                None, [
                    line._as_avatax_line() for line in self.lines
                ]
            ),
            u'Addresses': addresses,
        }

    @wrap_avatax_error
    def get_taxes_from_avatax(self):
        """
        Get the taxes from Avatax
        """
        if not self.sale_date:
            self.raise_user_error("Date is required to compute tax")

        if not self.warehouse:
            self.raise_user_error("Warehouse must be defined to compute tax")

        if not self.warehouse.address:
            self.raise_user_error("Warehouse does not have address")

        data = self._get_avatax_data()

        client_api = self.company.avatax_api()
        return client_api.tax_get_detailed(**data)

    def build_error_message_from_avalara(self, messages):
        """
        Build the error message from Avalra
        """
        # Default message
        message_string = 'Tax computation with Avalara failed'

        for message in messages:
            message_string += "%s\n\n%s" % (message['Name'], message['Summary'])
            if message.get('Details'):
                message_string += "\n\nDetails: %s" % message['Details']

        return message_string

    def update_taxes_from_avatax(self):
        """
        Update the taxes from avatax for the iven order
        """
        Line = Pool().get('sale.line')
        Tax = Pool().get('account.tax')
        Sale = Pool().get('sale.sale')

        tax_update_date = datetime.utcnow()

        response = self.get_taxes_from_avatax()

        if response['ResultCode'] != 'Success':
            # Getting tax information failed. Show a message
            self.raise_user_error(
                self.build_error_message_from_avalara(
                    response.get('Messages', [])
                )
            )

        for line in response['TaxLines']:
            if 'TaxDetails' not in line:
                continue
            taxes = [
                Tax.get_matching_tax(tax_line)
                for tax_line in line['TaxDetails'] if Decimal(tax_line['Tax'])
            ]
            Line.write(
                [Line(int(line['LineNo']))], {'taxes': [('add', taxes)]}
            )

        # Temporarily disable the total check as returns screw this up
        #
        # total_tax_avalara = Decimal(response['TotalTax'])
        # tax_sale = Sale(self.id).tax_amount
        # if abs(total_tax_avalara - tax_sale) > Decimal('0.01'):
        #    self.raise_user_error(
        #        'Mismatch in tax computations.\n'
        #        'Tryton Total: %s\n'
        #        'Avalara Total: %s' % (tax_sale, total_tax_avalara)
        #    )
        self.write([self], {'tax_update_date': tax_update_date})

    def requires_tax_refresh(self):
        """
        Returns True if the taxes require refresh
        """
        SaleLine = Pool().get('sale.line')

        if self.tax_update_date is None:
            return True

        if self.write_date > self.tax_update_date:
            return True

        return bool(SaleLine.search([
                'OR',
                ('write_date', '>', self.tax_update_date),
                ('create_date', '>', self.tax_update_date),
        ]))

    @classmethod
    @ModelView.button
    @Workflow.transition('quotation')
    def quote(cls, sales):
        super(Sale, cls).quote(sales)

        for sale in sales:
            if sale.company.enable_avatax and sale.requires_tax_refresh():
                sale.update_taxes_from_avatax()


class SaleLine:
    "Sale order line"
    __name__ = "sale.line"

    def _as_avatax_line(self):
        """
        Returns a JSON serializable dictionary of the line
        """
        if not self.product:
            return None

        return dict(
            LineNo=self.id,
            DestinationCode=self.sale.shipment_address.id,
            OriginCode=self.sale.warehouse.address.id,
            ItemCode=self.product.code,
            TaxCode=self.product.avatax_tax_code,
            Description=self.description,
            Qty=str(abs(self.quantity)),
            Amount=str(abs(self.amount)),
        )

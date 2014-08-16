# -*- coding: utf-8 -*-
"""
    sale


    :copyright: © 2013-2014 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from decimal import Decimal
from datetime import datetime

from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction
from trytond.model import ModelView, Workflow, fields

from .company import wrap_avatax_error

__all__ = ['Sale', 'SaleLine']
__metaclass__ = PoolMeta


class Sale:
    "Sale"
    __name__ = "sale.sale"

    tax_update_date = fields.DateTime('Tax Details Update Time', readonly=True)

    @wrap_avatax_error
    def get_taxes_from_avatax(self):
        """
        Get the taxes from Avatax
        """
        Company = Pool().get('company.company')

        if not self.sale_date:
            self.raise_user_error("Date is required to compute tax")

        if not self.warehouse:
            self.raise_user_error("Warehouse must be defined to compute tax")

        if not self.warehouse.address:
            self.raise_user_error("Warehouse does not have address")

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

        data = {
            u'DocDate': self.sale_date.strftime("%Y-%m-%d"),
            u'CustomerCode': self.party.code,
            u'Lines': filter(
                None, [
                    line._as_avatax_line() for line in self.lines
                ]
            ),
            u'Addresses': addresses,
        }

        company = Company(Transaction().context['company'])
        client_api = company.avatax_api()
        return client_api.tax_get_detailed(**data)

    def update_taxes_from_avatax(self):
        """
        Update the taxes from avatax for the iven order
        """
        Line = Pool().get('sale.line')
        Tax = Pool().get('account.tax')

        tax_update_date = datetime.utcnow()

        response = self.get_taxes_from_avatax()
        for line in response['TaxLines']:
            taxes = [
                Tax.get_matching_tax(tax_line)
                for tax_line in line['TaxDetails'] if Decimal(tax_line['Tax'])
            ]
            Line.write(
                [Line(int(line['LineNo']))], {'taxes': [('add', taxes)]}
            )

        assert Decimal(response['TotalTax']) == self.tax_amount
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
            Qty=str(self.quantity),
            Amount=str(self.amount),
        )

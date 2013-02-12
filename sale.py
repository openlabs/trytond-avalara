# -*- coding: utf-8 -*-
"""
    sale


    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from decimal import Decimal

from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction
from trytond.model import ModelView, Workflow

__metaclass__ = PoolMeta


class Sale:
    __name__ = "sale.sale"

    def get_taxes_from_avatax(self):
        """
        Get the taxes from Avatax
        """
        Company = Pool().get('company.company')

        if not self.sale_date:
            self.raise_user
        assert self.sale_date, "Date is required to compute tax"
        assert self.warehouse, "Warehouse must be defined to compute tax"
        assert self.warehouse.address, "Warehouse does not have address"

        invoice_address = self.invoice_address._as_avatax_address()
        invoice_address['AddressCode'] = self.invoice_address.id
        shipment_address = self.shipment_address._as_avatax_address()
        shipment_address['AddressCode'] = self.shipment_address.id
        warehouse_address = self.warehouse.address._as_avatax_address()
        warehouse_address['AddressCode'] = self.warehouse.address.id

        data = {
            u'DocDate': self.sale_date.strftime("%Y-%m-%d"),
            u'CustomerCode': self.party.code,
            u'Lines': filter(
                None, [
                    line._as_avatax_line() for line in self.lines
                ]
            ),
            u'Addresses': [
                invoice_address, shipment_address, warehouse_address
            ]
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

        response = self.get_taxes_from_avatax()
        for line in response['TaxLines']:
            taxes = [
                Tax.get_matching_tax(tax_line) \
                    for tax_line in line['TaxDetails']
                        if Decimal(tax_line['Tax'])
            ]
            Line.write(
                [Line(int(line['LineNo']))], {'taxes': [('set', taxes)]}
            )

        assert Decimal(response['TotalTax']) == self.tax_amount

    @classmethod
    @ModelView.button
    @Workflow.transition('quotation')
    def quote(cls, sales):
        for sale in sales:
            sale.check_for_quotation()
            sale.update_taxes_from_avatax()
        cls.set_reference(sales)


class SaleLine:
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

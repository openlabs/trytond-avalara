# -*- coding: utf-8 -*-
"""
    __init__

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.pool import Pool
from party import CustomerUsageType, Party, Address
from company import Company
from product import Product
from account import Tax, TaxCode
from sale import Sale, SaleLine


def register():
    Pool.register(
        CustomerUsageType,
        Party,
        Address,
        Company,
        Product,
        Tax,
        TaxCode,
        Sale,
        SaleLine,
        module='avalara', type_='model'
    )

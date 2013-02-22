# -*- coding: utf-8 -*-
"""
    product

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Product']

__metaclass__ = PoolMeta

class Product:
    "Product"
    __name__ = 'product.product'

    avatax_tax_code = fields.Char('Avatax Tax Code')

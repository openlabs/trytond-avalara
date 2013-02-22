# -*- coding: utf-8 -*-
"""
    __init__

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.pool import Pool
from .party import *
from .company import *
from .product import *
from .account import *
from .sale import *


def register():
    Pool.register(
        CustomerUsageType,
        Party,
        Address,
        Company,
        Product,
        Tax,
        Sale,
        SaleLine,
        module='avatax_calc', type_='model')

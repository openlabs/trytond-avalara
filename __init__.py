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
from .avatax import *


def register():
    Pool.register(
        Party,
        Company,
        Product,
        CustomerUsageType,
        module='avatax_calc', type_='model')

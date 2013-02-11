# -*- coding: utf-8 -*-
"""
    party

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Party']

__metaclass__ = PoolMeta

class Party:
    "Party"
    __name__ = 'party.party'

    auto_update_avatax = fields.Boolean('Auto Update Avatax')
    customer_usage_type = fields.Many2One(
        'avatax.customer_usage_type', 'Customer Usage Type'
    )

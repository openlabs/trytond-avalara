# -*- coding: utf-8 -*-
"""
    avatax

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
from trytond.model import ModelView, ModelSQL, fields

__all__ = ['CustomerUsageType']


class CustomerUsageType(ModelSQL, ModelView):
    "Customer Usage Type"
    __name__ = 'avatax.customer_usage_type'

    code = fields.Char('Code', required=True)
    name = fields.Char('Name', required=True)

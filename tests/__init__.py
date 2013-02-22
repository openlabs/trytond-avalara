# -*- coding: utf-8 -*-
"""
    __init__

    Test Suite for the avatax_calc module

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import unittest

import trytond.tests.test_tryton

from .test_view_depends import TestViewDependsCase


def suite():
    test_suite = trytond.tests.test_tryton.suite()
    test_suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestViewDependsCase)
    ])
    return test_suite

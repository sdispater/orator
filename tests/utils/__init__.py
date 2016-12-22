# -*- coding: utf-8 -*-
from flexmock import flexmock_teardown

from tests import OratorTestCase


class OratorUtilsTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

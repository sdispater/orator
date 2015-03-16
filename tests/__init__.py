# -*- coding: utf-8 -*-

import sys
import os
from unittest import TestCase

PY2 = sys.version_info[0] == 2

if PY2:
    import mock
else:
    import unittest.mock as mock


class EloquentTestCase(TestCase):

    def assertRegex(self, *args, **kwargs):
        if PY2:
            return self.assertRegexpMatches(*args, **kwargs)
        else:
            return super(EloquentTestCase, self).assertRegex(*args, **kwargs)

    def assertNotRegex(self, *args, **kwargs):
        if PY2:
            return self.assertNotRegexpMatches(*args, **kwargs)
        else:
            return super(EloquentTestCase, self).assertNotRegex(*args, **kwargs)

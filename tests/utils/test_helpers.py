import os

from flexmock import flexmock

from orator.utils import mkdir_p
from orator.utils import value
from tests.utils import OratorUtilsTestCase


class HelpersTest(OratorUtilsTestCase):
    pass


class ValueTest(HelpersTest):
    def test_none(self):
        self.assertIsNone(value(None))

    def test_scalar_int(self):
        self.assertEqual(1, value(1))

    def test_scalar_str(self):
        self.assertEqual('test', value('test'))

    def test_scalar_bool(self):
        self.assertEqual(True, value(True))

    def test_callable(self):
        def f():
            return 'test'

        self.assertEqual('test', value(f))


class MkdirPTest(HelpersTest):
    def test_success(self):
        mock_os = flexmock(os)
        mock_os.should_receive('makedirs').with_args('/test/path', 0o777)
        mkdir_p('/test/path', 0o777)
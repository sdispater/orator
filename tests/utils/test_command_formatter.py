# -*- coding: utf-8 -*-
from flexmock import flexmock
from pygments.token import Token
from pygments.util import OptionError

from orator.utils.command_formatter import CommandFormatter, COMMAND_COLORS
from tests.utils import OratorUtilsTestCase


class CommandFormatterTest(OratorUtilsTestCase):
    Miss = Token.Miss
    Hit = Token.Hit

    TEST_COLOR_SCHEME = {
        Token: ('', ''),
        Hit: ('hit.light', 'hit.dark'),
        Hit.Specific: ('hit.specific.light', 'hit.specific.dark'),
        Hit.Specific.Child: ('hit.specific.child.light', 'hit.specific.child.dark'),
    }

    EMPTY_TOKEN_SOURCE = []

    SIMPLE_TOKEN_SOURCE = [
        (Hit, 'token')
    ]

    MULTI_TOKEN_SOURCE = [
        (Hit, 'first token'),
        (Miss, 'second token'),
    ]

    MULTI_LINE_TOKEN_SOURCE = [
        (Hit, 'first line\nsecond line\n'),
        (Miss, 'third line\nfourth line\n'),
    ]


class InitTest(CommandFormatterTest):
    def test_bg_defaults_darkbg_off(self):
        formatter = CommandFormatter()
        self.assertFalse(formatter.darkbg)

    def test_bg_light(self):
        formatter = CommandFormatter(bg='light')
        self.assertFalse(formatter.darkbg)

    def test_bg_dark(self):
        formatter = CommandFormatter(bg='dark')
        self.assertTrue(formatter.darkbg)

    def test_invalid_bg(self):
        with self.assertRaises(OptionError):
            CommandFormatter(bg='invalid')

    def test_default_colorscheme(self):
        formatter = CommandFormatter()
        self.assertEqual(formatter.colorscheme, COMMAND_COLORS)

    def test_custom_colorscheme(self):
        formatter = CommandFormatter(colorscheme='custom')
        self.assertEqual(formatter.colorscheme, 'custom')

    def test_default_linenos(self):
        formatter = CommandFormatter()
        self.assertFalse(formatter.linenos)

    def test_linenos_off(self):
        formatter = CommandFormatter(linenos=False)
        self.assertFalse(formatter.linenos)

    def test_linenos_on(self):
        formatter = CommandFormatter(linenos=True)
        self.assertTrue(formatter.linenos)


class WriteLinenoTest(CommandFormatterTest):
    def test_first_line(self):
        formatter = CommandFormatter()
        outfile = flexmock()
        outfile.should_receive('write').with_args('0001: ').once()
        formatter._write_lineno(outfile)

    def test_subsequent_lines(self):
        formatter = CommandFormatter()
        formatter._lineno = 10
        outfile = flexmock()
        outfile.should_receive('write').with_args('\n0011: ').once()
        formatter._write_lineno(outfile)

    def test_huge_lines(self):
        formatter = CommandFormatter()
        formatter._lineno = 10000
        outfile = flexmock()
        outfile.should_receive('write').with_args('\n10001: ').once()
        formatter._write_lineno(outfile)


class GetColorTest(CommandFormatterTest):
    def get_color(self, ttype, bg):
        formatter = CommandFormatter(bg=bg, colorscheme=self.TEST_COLOR_SCHEME)
        return formatter._get_color(ttype)

    def get_light_color(self, ttype):
        return self.get_color(ttype, 'light')

    def get_dark_color(self, ttype):
        return self.get_color(ttype, 'dark')

    def test_miss_light(self):
        self.assertEqual(self.get_light_color(self.Miss), '')

    def test_miss_dark(self):
        self.assertEqual(self.get_dark_color(self.Miss), '')

    def test_hit_light(self):
        self.assertEqual(self.get_light_color(self.Hit), 'hit.light')

    def test_hit_dark(self):
        self.assertEqual(self.get_dark_color(self.Hit), 'hit.dark')

    def test_hit_specific_light(self):
        self.assertEqual(self.get_light_color(self.Hit.Specific), 'hit.specific.light')

    def test_hit_specific_dark(self):
        self.assertEqual(self.get_dark_color(self.Hit.Specific), 'hit.specific.dark')

    def test_hit_miss_light(self):
        self.assertEqual(self.get_light_color(self.Hit.Miss), 'hit.light')

    def test_hit_miss_dark(self):
        self.assertEqual(self.get_dark_color(self.Hit.Miss), 'hit.dark')

    def test_hit_specific_child_light(self):
        self.assertEqual(self.get_light_color(self.Hit.Specific.Child), 'hit.specific.child.light')

    def test_hit_specific_child_dark(self):
        self.assertEqual(self.get_dark_color(self.Hit.Specific.Child), 'hit.specific.child.dark')

    def test_hit_specific_miss_light(self):
        self.assertEqual(self.get_light_color(self.Hit.Specific.Miss), 'hit.specific.light')

    def test_hit_specific_miss_dark(self):
        self.assertEqual(self.get_dark_color(self.Hit.Specific.Miss), 'hit.specific.dark')

    def test_hit_miss_child_light(self):
        self.assertEqual(self.get_light_color(self.Hit.Miss.Child), 'hit.light')

    def test_hit_miss_child_dark(self):
        self.assertEqual(self.get_dark_color(self.Hit.Miss.Child), 'hit.dark')


class FormatUnencodedTest(CommandFormatterTest):
    class Outfile(object):
        def __init__(self):
            self.buffer = ''

        def write(self, value):
            self.buffer += value

    def format(self, tokensource, linenos):
        outfile = self.Outfile()
        formatter = CommandFormatter(colorscheme=self.TEST_COLOR_SCHEME, linenos=linenos)
        formatter.format_unencoded(tokensource, outfile)
        return outfile.buffer

    def test_empty_source_without_linenos(self):
        actual = self.format(self.EMPTY_TOKEN_SOURCE, linenos=False)
        self.assertEqual('', actual)

    def test_empty_source_with_linenos(self):
        actual = self.format(self.EMPTY_TOKEN_SOURCE, linenos=True)
        self.assertEqual('0001: \n', actual)

    def test_simple_source_without_linenos(self):
        actual = self.format(self.SIMPLE_TOKEN_SOURCE, linenos=False)
        self.assertEqual('<hit.light>token</>', actual)

    def test_simple_source_with_linenos(self):
        actual = self.format(self.SIMPLE_TOKEN_SOURCE, linenos=True)
        self.assertEqual('0001: <hit.light>token</>\n', actual)

    def test_multi_source_without_linenos(self):
        actual = self.format(self.MULTI_TOKEN_SOURCE, linenos=False)
        self.assertEqual('<hit.light>first token</>second token', actual)

    def test_multi_source_with_linenos(self):
        actual = self.format(self.MULTI_TOKEN_SOURCE, linenos=True)
        self.assertEqual('0001: <hit.light>first token</>second token\n', actual)

    def test_multi_line_source_without_linenos(self):
        actual = self.format(self.MULTI_LINE_TOKEN_SOURCE, linenos=False)
        self.assertEqual('<hit.light>first line</>\n'
                         '<hit.light>second line</>\n'
                         'third line\n'
                         'fourth line\n', actual)

    def test_multi_line_source_with_linenos(self):
        actual = self.format(self.MULTI_LINE_TOKEN_SOURCE, linenos=True)
        self.assertEqual('0001: <hit.light>first line</>\n'
                         '0002: <hit.light>second line</>\n'
                         '0003: third line\n'
                         '0004: fourth line\n'
                         '0005: \n', actual)


class FormatTest(CommandFormatterTest):
    class Outfile(object):
        def __init__(self):
            self.buffer = ''

        def write(self, value):
            self.buffer += value

    def format(self, tokensource, linenos):
        outfile = self.Outfile()
        formatter = CommandFormatter(colorscheme=self.TEST_COLOR_SCHEME, linenos=linenos)
        formatter.format(tokensource, outfile)
        return outfile.buffer

    def test_empty_source_without_linenos(self):
        actual = self.format(self.EMPTY_TOKEN_SOURCE, linenos=False)
        self.assertEqual('', actual)

    def test_empty_source_with_linenos(self):
        actual = self.format(self.EMPTY_TOKEN_SOURCE, linenos=True)
        self.assertEqual('0001: \n', actual)

    def test_simple_source_without_linenos(self):
        actual = self.format(self.SIMPLE_TOKEN_SOURCE, linenos=False)
        self.assertEqual('<hit.light>token</>', actual)

    def test_simple_source_with_linenos(self):
        actual = self.format(self.SIMPLE_TOKEN_SOURCE, linenos=True)
        self.assertEqual('0001: <hit.light>token</>\n', actual)

    def test_multi_source_without_linenos(self):
        actual = self.format(self.MULTI_TOKEN_SOURCE, linenos=False)
        self.assertEqual('<hit.light>first token</>second token', actual)

    def test_multi_source_with_linenos(self):
        actual = self.format(self.MULTI_TOKEN_SOURCE, linenos=True)
        self.assertEqual('0001: <hit.light>first token</>second token\n', actual)

    def test_multi_line_source_without_linenos(self):
        actual = self.format(self.MULTI_LINE_TOKEN_SOURCE, linenos=False)
        self.assertEqual('<hit.light>first line</>\n'
                         '<hit.light>second line</>\n'
                         'third line\n'
                         'fourth line\n', actual)

    def test_multi_line_source_with_linenos(self):
        actual = self.format(self.MULTI_LINE_TOKEN_SOURCE, linenos=True)
        self.assertEqual('0001: <hit.light>first line</>\n'
                         '0002: <hit.light>second line</>\n'
                         '0003: third line\n'
                         '0004: fourth line\n'
                         '0005: \n', actual)

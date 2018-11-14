# -*- coding: utf-8 -*-

from pygments.formatter import Formatter
from pygments.token import (
    Keyword,
    Name,
    Comment,
    String,
    Error,
    Number,
    Operator,
    Generic,
    Token,
    Whitespace,
)
from pygments.util import get_choice_opt


COMMAND_COLORS = {
    Token: ("", ""),
    Whitespace: ("fg=white", "fg=black;options=bold"),
    Comment: ("fg=white", "fg=black;options=bold"),
    Comment.Preproc: ("fg=cyan", "fg=cyan;options=bold"),
    Keyword: ("fg=blue", "fg=blue;options=bold"),
    Keyword.Type: ("fg=cyan", "fg=cyan;options=bold"),
    Operator.Word: ("fg=magenta", "fg=magenta;options=bold"),
    Name.Builtin: ("fg=cyan", "fg=cyan;options=bold"),
    Name.Function: ("fg=green", "fg=green;option=bold"),
    Name.Namespace: ("fg=cyan;options=underline", "fg=cyan;options=bold,underline"),
    Name.Class: ("fg=green;options=underline", "fg=green;options=bold,underline"),
    Name.Exception: ("fg=cyan", "fg=cyan;options=bold"),
    Name.Decorator: ("fg=black;options=bold", "fg=white"),
    Name.Variable: ("fg=red", "fg=red;options=bold"),
    Name.Constant: ("fg=red", "fg=red;options=bold"),
    Name.Attribute: ("fg=cyan", "fg=cyan;options=bold"),
    Name.Tag: ("fg=blue;options=bold", "fg=blue;options=bold"),
    String: ("fg=yellow", "fg=yellow"),
    Number: ("fg=blue", "fg=blue;options=bold"),
    Generic.Deleted: ("fg=red;options=bold", "fg=red;options=bold"),
    Generic.Inserted: ("fg=green", "fg=green;options=bold"),
    Generic.Heading: ("options=bold", "option=bold"),
    Generic.Subheading: ("fg=magenta;options=bold", "fg=magenta;options=bold"),
    Generic.Prompt: ("options=bold", "options=bold"),
    Generic.Error: ("fg=red;options=bold", "fg=red;options=bold"),
    Error: ("fg=red;options=bold,underline", "fg=red;options=bold,underline"),
}


class CommandFormatter(Formatter):
    r"""
    Format tokens with Cleo color sequences, for output in a text console.
    Color sequences are terminated at newlines, so that paging the output
    works correctly.

    The `get_style_defs()` method doesn't do anything special since there is
    no support for common styles.

    Options accepted:

    `bg`
        Set to ``"light"`` or ``"dark"`` depending on the terminal's background
        (default: ``"light"``).

    `colorscheme`
        A dictionary mapping token types to (lightbg, darkbg) color names or
        ``None`` (default: ``None`` = use builtin colorscheme).

    `linenos`
        Set to ``True`` to have line numbers on the terminal output as well
        (default: ``False`` = no line numbers).
    """
    name = "Command"
    aliases = ["command"]
    filenames = []

    def __init__(self, **options):
        Formatter.__init__(self, **options)
        self.darkbg = (
            get_choice_opt(options, "bg", ["light", "dark"], "light") == "dark"
        )
        self.colorscheme = options.get("colorscheme", None) or COMMAND_COLORS
        self.linenos = options.get("linenos", False)
        self._lineno = 0

    def format(self, tokensource, outfile):
        return Formatter.format(self, tokensource, outfile)

    def _write_lineno(self, outfile):
        self._lineno += 1
        outfile.write("%s%04d: " % (self._lineno != 1 and "\n" or "", self._lineno))

    def _get_color(self, ttype):
        # self.colorscheme is a dict containing usually generic types, so we
        # have to walk the tree of dots.  The base Token type must be a key,
        # even if it's empty string, as in the default above.
        colors = self.colorscheme.get(ttype)
        while colors is None:
            ttype = ttype.parent
            colors = self.colorscheme.get(ttype)
        return colors[self.darkbg]

    def format_unencoded(self, tokensource, outfile):
        if self.linenos:
            self._write_lineno(outfile)

        for ttype, value in tokensource:
            color = self._get_color(ttype)

            for line in value.splitlines(True):
                if color:
                    outfile.write("<%s>%s</>" % (color, line.rstrip("\n")))
                else:
                    outfile.write(line.rstrip("\n"))
                if line.endswith("\n"):
                    if self.linenos:
                        self._write_lineno(outfile)
                    else:
                        outfile.write("\n")

        if self.linenos:
            outfile.write("\n")

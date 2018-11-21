# -*- coding: utf-8 -*-

import re


class Qmarker(object):

    RE_QMARK = re.compile(r"\?\?|\?|%")

    @classmethod
    def qmark(cls, query):
        """
        Convert a "qmark" query into "format" style.
        """

        def sub_sequence(m):
            s = m.group(0)
            if s == "??":
                return "?"
            if s == "%":
                return "%%"
            else:
                return "%s"

        return cls.RE_QMARK.sub(sub_sequence, query)

    @classmethod
    def denullify(cls, args):
        for arg in args:
            if arg is not None:
                yield arg
            else:
                yield ()


qmark = Qmarker.qmark
denullify = Qmarker.denullify

# -*- coding: utf-8 -*-


class KeywordList(object):

    KEYWORDS = []

    def is_keyword(self, word):
        return word.upper() in self.KEYWORDS

    def get_name(self):
        raise NotImplementedError

# -*- coding: utf-8 -*-

import re
import binascii
from ..utils import encode


class AbstractAsset(object):

    _name = None

    _namespace = None

    _quoted = False

    def _set_name(self, name):
        """
        Sets the name of this asset.

        :param name: The name of the asset
        :type name: str
        """
        if self._is_identifier_quoted(name):
            self._quoted = True
            name = self._trim_quotes(name)

        if "." in name:
            parts = name.split(".", 1)
            self._namespace = parts[0]
            name = parts[1]

        self._name = name

    def _is_in_default_namespace(self, default_namespace):
        return self._namespace == default_namespace or self._namespace is None

    def get_namespace_name(self):
        return self._namespace

    def get_shortest_name(self, default_namespace):
        shortest_name = self.get_name()
        if self._namespace == default_namespace:
            shortest_name = self._name

        return shortest_name.lower()

    def get_full_qualified_name(self, default_namespace):
        name = self.get_name()
        if not self._namespace:
            name = default_namespace + "." + name

        return name.lower()

    def is_quoted(self):
        return self._quoted

    def _is_identifier_quoted(self, identifier):
        return len(identifier) > 0 and (
            identifier[0] == "`" or identifier[0] == '"' or identifier[0] == "["
        )

    def _trim_quotes(self, identifier):
        return re.sub('[`"\[\]]', "", identifier)

    def get_name(self):
        if self._namespace:
            return self._namespace + "." + self._name

        return self._name

    def get_quoted_name(self, platform):
        keywords = platform.get_reserved_keywords_list()
        parts = self.get_name().split(".")
        for k, v in enumerate(parts):
            if self._quoted or keywords.is_keyword(v):
                parts[k] = platform.quote_identifier(v)

        return ".".join(parts)

    def _generate_identifier_name(self, columns, prefix="", max_size=30):
        """
        Generates an identifier from a list of column names obeying a certain string length.
        """
        hash = ""
        for column in columns:
            hash += "%x" % binascii.crc32(encode(str(column)))

        return (prefix + "_" + hash)[:max_size]

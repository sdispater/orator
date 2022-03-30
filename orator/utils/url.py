# -*- coding: utf-8 -*-

# engine/url.py
# Copyright (C) 2005-2014 the SQLAlchemy authors and contributors
# <see AUTHORS file>
#
# This module is part of SQLAlchemy and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

"""Provides the :class:`~sqlalchemy.engine.url.URL` class which encapsulates
information about a database connection specification.

The URL object is created automatically when
:func:`~sqlalchemy.engine.create_engine` is called with a string
argument; alternatively, the URL is a public-facing construct which can
be used directly and is also accepted directly by ``create_engine()``.
"""

import re
from . import parse_qsl, unquote_plus, unquote, basestring, PY2
from ..exceptions import ArgumentError


class URL(object):
    """
    Represent the components of a URL used to connect to a database.

    All initialization parameters are available as public attributes.

    :param drivername: the name of the database backend.

    :param username: The user name.

    :param password: database password.

    :param host: The name of the host.

    :param port: The port number.

    :param database: The database name.

    :param query: A dictionary of options to be passed to the
      dialect and/or the DBAPI upon connect.

    """

    def __init__(
        self,
        drivername,
        username=None,
        password=None,
        host=None,
        port=None,
        database=None,
        query=None,
    ):
        self.drivername = drivername
        self.username = username
        self.password = password
        self.host = host
        if port is not None:
            self.port = int(port)
        else:
            self.port = None
        self.database = database
        self.query = query or {}

    def __to_string__(self, hide_password=True):
        s = self.drivername + "://"
        if self.username is not None:
            s += _rfc_1738_quote(self.username)
            if self.password is not None:
                s += ":" + ("***" if hide_password else _rfc_1738_quote(self.password))
            s += "@"
        if self.host is not None:
            if ":" in self.host:
                s += "[%s]" % self.host
            else:
                s += self.host
        if self.port is not None:
            s += ":" + str(self.port)
        if self.database is not None:
            s += "/" + self.database
        if self.query:
            keys = list(self.query)
            keys.sort()
            s += "?" + "&".join("%s=%s" % (k, self.query[k]) for k in keys)
        return s

    def __str__(self):
        return self.__to_string__(hide_password=False)

    def __repr__(self):
        return self.__to_string__()

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return (
            isinstance(other, URL)
            and self.drivername == other.drivername
            and self.username == other.username
            and self.password == other.password
            and self.host == other.host
            and self.database == other.database
            and self.query == other.query
        )

    def get_backend_name(self):
        if "+" not in self.drivername:
            return self.drivername
        else:
            return self.drivername.split("+")[0]

    def get_driver_name(self):
        if "+" not in self.drivername:
            return self.get_dialect().driver
        else:
            return self.drivername.split("+")[1]

    def get_dialect(self):
        """Return the SQLAlchemy database dialect class corresponding
        to this URL's driver name.
        """

        if "+" not in self.drivername:
            name = self.drivername
        else:
            name = self.drivername.replace("+", ".")
        cls = registry.load(name)
        # check for legacy dialects that
        # would return a module with 'dialect' as the
        # actual class
        if (
            hasattr(cls, "dialect")
            and isinstance(cls.dialect, type)
            and issubclass(cls.dialect, Dialect)
        ):
            return cls.dialect
        else:
            return cls


def make_url(name_or_url):
    """Given a string or unicode instance, produce a new URL instance.

    The given string is parsed according to the RFC 1738 spec.  If an
    existing URL object is passed, just returns the object.
    """

    if isinstance(name_or_url, basestring):
        return _parse_rfc1738_args(name_or_url)
    else:
        return name_or_url


def _parse_rfc1738_args(name):
    pattern = re.compile(
        r"""
            (?P<name>[\w\+]+)://
            (?:
                (?P<username>[^:/]*)
                (?::(?P<password>.*))?
            @)?
            (?:
                (?:
                    \[(?P<ipv6host>[^/]+)\] |
                    (?P<ipv4host>[^/:]+)
                )?
                (?::(?P<port>[^/]*))?
            )?
            (?:/(?P<database>.*))?
            """,
        re.X,
    )

    m = pattern.match(name)
    if m is not None:
        components = m.groupdict()
        if components["database"] is not None:
            tokens = components["database"].split("?", 2)
            components["database"] = tokens[0]
            query = (len(tokens) > 1 and dict(parse_qsl(tokens[1]))) or None
            if PY2 and query is not None:
                query = dict((k.encode("ascii"), query[k]) for k in query)
        else:
            query = None
        components["query"] = query

        if components["username"] is not None:
            components["username"] = _rfc_1738_unquote(components["username"])

        if components["password"] is not None:
            components["password"] = _rfc_1738_unquote(components["password"])

        ipv4host = components.pop("ipv4host")
        ipv6host = components.pop("ipv6host")
        components["host"] = ipv4host or ipv6host
        name = components.pop("name")
        return URL(name, **components)
    else:
        raise ArgumentError("Could not parse rfc1738 URL from string '%s'" % name)


def _rfc_1738_quote(text):
    return re.sub(r"[:@/]", lambda m: "%%%X" % ord(m.group(0)), text)


def _rfc_1738_unquote(text):
    return unquote(text)


def _parse_keyvalue_args(name):
    m = re.match(r"(\w+)://(.*)", name)
    if m is not None:
        (name, args) = m.group(1, 2)
        opts = dict(parse_qsl(args))
        return URL(name, *opts)
    else:
        return None

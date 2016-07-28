# -*- coding: utf-8 -*-

from .base_collection import BaseCollection

try:
    from ._collection import Collection as ExtCollection
except ImportError:
    class ExtCollection:
        pass


class Collection(ExtCollection, BaseCollection):

    pass

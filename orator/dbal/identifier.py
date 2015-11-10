# -*- coding: utf-8 -*-

from .abstract_asset import AbstractAsset


class Identifier(AbstractAsset):

    def __init__(self, identifier):
        self._set_name(identifier)

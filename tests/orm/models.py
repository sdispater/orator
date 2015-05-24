# -*- coding: utf-8 -*-

from orator.orm import Model


class User(Model):

    __fillable__ = ['name']

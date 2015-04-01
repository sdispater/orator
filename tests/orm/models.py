# -*- coding: utf-8 -*-

from eloquent.orm import Model


class User(Model):

    __fillable__ = ['name']

# -*- coding: utf-8 -*-


class Scope(object):
    def apply(self, builder, model):
        """
        Apply the scope to a given query builder.

        :param builder: The query builder
        :type builder: orator.orm.Builder

        :param model: The model
        :type model: orator.orm.Model
        """
        raise NotImplementedError

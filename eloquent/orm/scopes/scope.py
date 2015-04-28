# -*- coding: utf-8 -*-


class Scope(object):

    def apply(self, builder, model):
        """
        Apply the scope to a given query builder.

        :param builder: The query builder
        :type builder: eloquent.orm.Builder

        :param model: The model
        :type model: eloquent.orm.Model
        """
        raise NotImplementedError

    def remove(self, builder, model):
        """
        Remove the scope from a given query builder.

        :param builder: The query builder
        :type builder: eloquent.orm.Builder

        :param model: The model
        :type model: eloquent.orm.Model
        """
        raise NotImplementedError

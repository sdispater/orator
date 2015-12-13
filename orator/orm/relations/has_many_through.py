# -*- coding: utf-8 -*-

from ...query.expression import QueryExpression
from .relation import Relation
from .result import Result


class HasManyThrough(Relation):

    def __init__(self, query, far_parent, parent, first_key, second_key):
        """
        :param query: A Builder instance
        :type query: Builder

        :param far_parent: The far parent model
        :type far_parent: Model

        :param parent: The parent model
        :type parent: Model

        :type first_key: str
        :type second_key: str
        """
        self._first_key = first_key
        self._second_key = second_key
        self._far_parent = far_parent

        super(HasManyThrough, self).__init__(query, parent)

    def add_constraints(self):
        """
        Set the base constraints on the relation query.

        :rtype: None
        """
        parent_table = self._parent.get_table()

        self._set_join()

        if self._constraints:
            self._query.where('%s.%s' % (parent_table, self._first_key), '=', self._far_parent.get_key())

    def get_relation_count_query(self, query, parent):
        """
        Add the constraints for a relationship count query.

        :type query: Builder
        :type parent: Builder

        :rtype: Builder
        """
        parent_table = self._parent.get_table()

        self._set_join(query)

        query.select(QueryExpression('COUNT(*)'))

        key = self.wrap('%s.%s' % (parent_table, self._first_key))

        return query.where(self.get_has_compare_key(), '=', QueryExpression(key))

    def _set_join(self, query=None):
        """
        Set the join clause for the query.
        """
        if not query:
            query = self._query

        foreign_key = '%s.%s' % (self._related.get_table(), self._second_key)

        query.join(self._parent.get_table(), self.get_qualified_parent_key_name(), '=', foreign_key)

    def add_eager_constraints(self, models):
        """
        Set the constraints for an eager load of the relation.

        :type models: list
        """
        table = self._parent.get_table()

        self._query.where_in('%s.%s' % (table, self._first_key), self.get_keys(models))

    def init_relation(self, models, relation):
        """
        Initialize the relation on a set of models.

        :type models: list
        :type relation:  str
        """
        for model in models:
            model.set_relation(relation, Result(self._related.new_collection(), self, model))

        return models

    def match(self, models, results, relation):
        """
        Match the eagerly loaded results to their parents.

        :type models: list
        :type results: Collection
        :type relation:  str
        """
        dictionary = self._build_dictionary(results)

        for model in models:
            key = model.get_key()

            if key in dictionary:
                value = Result(self._related.new_collection(dictionary[key]), self, model)
            else:
                value = Result(self._related.new_collection(), self, model)

            model.set_relation(relation, value)

        return models

    def _build_dictionary(self, results):
        """
        Build model dictionary keyed by the relation's foreign key.

        :param results: The results
        :type results: Collection

        :rtype: dict
        """
        foreign = self._first_key

        dictionary = {}

        for result in results:
            key = getattr(result, foreign)
            if key not in dictionary:
                dictionary[key] = []

            dictionary[key].append(result)

        return dictionary

    def get_results(self):
        """
        Get the results of the relationship.
        """
        return self.get()

    def get(self, columns=None):
        """
        Execute the query as a "select" statement.

        :type columns: list

        :rtype: orator.Collection
        """
        if columns is None:
            columns = ['*']

        select = self._get_select_columns(columns)

        models = self._query.add_select(*select).get_models()

        if len(models) > 0:
            models = self._query.eager_load_relations(models)

        return self._related.new_collection(models)

    def _get_select_columns(self, columns=None):
        """
        Set the select clause for the relation query.

        :param columns: The columns
        :type columns: list

        :rtype: list
        """
        if columns == ['*'] or columns is None:
            columns = ['%s.*' % self._related.get_table()]

        return columns + ['%s.%s' % (self._parent.get_table(), self._first_key)]

    def get_has_compare_key(self):
        return self._far_parent.get_qualified_key_name()

    def _new_instance(self, model):
        return HasManyThrough(
            self.new_query(),
            model,
            self._parent,
            self._first_key,
            self._second_key
        )

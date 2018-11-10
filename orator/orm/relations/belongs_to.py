# -*- coding: utf-8 -*-

from ...query.expression import QueryExpression
from .relation import Relation
from .result import Result


class BelongsTo(Relation):
    def __init__(self, query, parent, foreign_key, other_key, relation):
        """
        :param query: A Builder instance
        :type query: Builder

        :param parent: The parent model
        :type parent: Model

        :param foreign_key: The foreign key
        :type foreign_key: str

        :param other_key: The other key
        :type other_key: str

        :param relation: The relation name
        :type relation: str
        """
        self._other_key = other_key
        self._relation = relation
        self._foreign_key = foreign_key

        super(BelongsTo, self).__init__(query, parent)

    def get_results(self):
        """
        Get the results of the relationship.
        """
        if self._query is None:
            return None

        return self._query.first()

    def add_constraints(self):
        """
        Set the base constraints on the relation query.

        :rtype: None
        """
        if self._constraints:
            foreign_key = getattr(self._parent, self._foreign_key, None)
            if foreign_key is None:
                self._query = None
            else:
                table = self._related.get_table()

                self._query.where(
                    "{}.{}".format(table, self._other_key), "=", foreign_key
                )

    def get_relation_count_query(self, query, parent):
        """
        Add the constraints for a relationship count query.

        :type query: orator.orm.Builder
        :type parent: orator.orm.Builder

        :rtype: Builder
        """
        query.select(QueryExpression("COUNT(*)"))

        other_key = self.wrap(
            "%s.%s" % (query.get_model().get_table(), self._other_key)
        )

        return query.where(
            self.get_qualified_foreign_key(), "=", QueryExpression(other_key)
        )

    def add_eager_constraints(self, models):
        """
        Set the constraints for an eager load of the relation.

        :type models: list
        """
        key = "%s.%s" % (self._related.get_table(), self._other_key)

        self._query.where_in(key, self._get_eager_model_keys(models))

    def _get_eager_model_keys(self, models):
        """
        Gather the keys from a list of related models.

        :type models: list

        :rtype: list
        """
        keys = []

        for model in models:
            value = getattr(model, self._foreign_key)

            if value is not None and value not in keys:
                keys.append(value)

        if not len(keys):
            return [0]

        return keys

    def init_relation(self, models, relation):
        """
        Initialize the relation on a set of models.

        :type models: list
        :type relation:  str
        """
        for model in models:
            model.set_relation(relation, Result(None, self, model))

        return models

    def match(self, models, results, relation):
        """
        Match the eagerly loaded results to their parents.

        :type models: list
        :type results: Collection
        :type relation:  str
        """
        foreign = self._foreign_key

        other = self._other_key

        dictionary = {}

        for result in results:
            dictionary[result.get_attribute(other)] = result

        for model in models:
            value = getattr(model, foreign)

            if value in dictionary:
                results = Result(dictionary[value], self, model)
            else:
                results = Result(None, self, model)

            model.set_relation(relation, results)

        return models

    def associate(self, model):
        """
        Associate the model instance to the given parent.

        :type model: orator.Model

        :rtype: orator.Model
        """
        self._parent.set_attribute(
            self._foreign_key, model.get_attribute(self._other_key)
        )

        return self._parent.set_relation(
            self._relation, Result(model, self, self._parent)
        )

    def dissociate(self):
        """
        Dissociate previously associated model from the given parent.

        :rtype: orator.Model
        """
        self._parent.set_attribute(self._foreign_key, None)

        return self._parent.set_relation(
            self._relation, Result(None, self, self._parent)
        )

    def update(self, _attributes=None, **attributes):
        """
        Update the parent model on the relationship.

        :param attributes: The update attributes
        :type attributes: dict

        :rtype: mixed
        """
        if _attributes is not None:
            attributes.update(_attributes)

        instance = self.get_results()

        return instance.fill(attributes).save()

    def get_foreign_key(self):
        return self._foreign_key

    def get_qualified_foreign_key(self):
        return "%s.%s" % (self._parent.get_table(), self._foreign_key)

    def get_other_key(self):
        return self._other_key

    def get_qualified_other_key_name(self):
        return "%s.%s" % (self._related.get_table(), self._other_key)

    def _new_instance(self, model):
        return BelongsTo(
            self.new_query(), model, self._foreign_key, self._other_key, self._relation
        )

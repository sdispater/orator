# -*- coding: utf-8 -*-

from .has_one_or_many import HasOneOrMany
from .result import Result


class HasMany(HasOneOrMany):

    def get_results(self):
        """
        Get the results of the relationship.
        """
        return self._query.get()

    def init_relation(self, models, relation):
        """
        Initialize the relation on a set of models.

        :type models: list
        :type relation: str
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
        return self.match_many(models, results, relation)

    def _new_instance(self, model):
        return HasMany(
            self.new_query(),
            model,
            self._foreign_key,
            self._local_key
        )

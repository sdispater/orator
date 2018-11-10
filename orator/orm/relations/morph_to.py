# -*- coding: utf-8 -*-

from .belongs_to import BelongsTo
from ..collection import Collection
from ...support.collection import Collection as BaseCollection
from .result import Result


class MorphTo(BelongsTo):
    def __init__(self, query, parent, foreign_key, other_key, type, relation):
        """
        :type query: orator.orm.Builder

        :param parent: The parent model
        :type parent: Model

        :param query:
        :param parent:

        :param foreign_key: The foreign key of the parent model
        :type foreign_key: str

        :param other_key: The local key of the parent model
        :type other_key: str

        :param type: The morph type
        :type type: str

        :param relation: The relation name
        :type relation: str
        """
        self._morph_type = type

        self._models = Collection()
        self._dictionary = {}
        self._with_trashed = False

        super(MorphTo, self).__init__(query, parent, foreign_key, other_key, relation)

    def add_eager_constraints(self, models):
        """
        Set the constraints for an eager load of the relation.

        :type models: list
        """
        self._models = Collection.make(models)
        self._build_dictionary(models)

    def _build_dictionary(self, models):
        """
        Build a dictionary with the models.

        :param models: The models
        :type models: Collection
        """
        for model in models:
            key = getattr(model, self._morph_type, None)
            if key:
                foreign = getattr(model, self._foreign_key)
                if key not in self._dictionary:
                    self._dictionary[key] = {}

                if foreign not in self._dictionary[key]:
                    self._dictionary[key][foreign] = []

                self._dictionary[key][foreign].append(model)

    def match(self, models, results, relation):
        """
        Match the eagerly loaded results to their parents.

        :type models: Collection
        :type results: Collection
        :type relation:  str
        """
        return models

    def associate(self, model):
        """
        Associate the model instance to the given parent.

        :type model: orator.Model

        :rtype: orator.Model
        """
        self._parent.set_attribute(self._foreign_key, model.get_key())
        self._parent.set_attribute(self._morph_type, model.get_morph_name())

        return self._parent.set_relation(
            self._relation, Result(model, self, self._parent)
        )

    def get_eager(self):
        """
        Get the relationship for eager loading.

        :rtype: Collection
        """
        for type in self._dictionary.keys():
            self._match_to_morph_parents(type, self._get_results_by_type(type))

        return self._models

    def _match_to_morph_parents(self, type, results):
        """
        Match the results for a given type to their parent.

        :param type: The parent type
        :type type: str

        :param results: The results to match to their parent
        :type results: Collection
        """
        for result in results:
            if result.get_key() in self._dictionary.get(type, []):
                for model in self._dictionary[type][result.get_key()]:
                    model.set_relation(
                        self._relation, Result(result, self, model, related=result)
                    )

    def _get_results_by_type(self, type):
        """
        Get all the relation results for a type.

        :param type: The type
        :type type: str

        :rtype: Collection
        """
        instance = self._create_model_by_type(type)

        key = instance.get_key_name()

        query = instance.new_query()

        query = self._use_with_trashed(query)

        return query.where_in(key, self._gather_keys_by_type(type).all()).get()

    def _gather_keys_by_type(self, type):
        """
        Gather all of the foreign keys for a given type.

        :param type: The type
        :type type: str

        :rtype: BaseCollection
        """
        foreign = self._foreign_key

        keys = (
            BaseCollection.make(list(self._dictionary[type].values()))
            .map(lambda models: getattr(models[0], foreign))
            .unique()
        )

        return keys

    def _create_model_by_type(self, type):
        """
        Create a new model instance by type.

        :rtype: Model
        """
        klass = self._parent.get_actual_class_for_morph(type)

        return klass()

    def get_morph_type(self):
        return self._morph_type

    def get_dictionary(self):
        return self._dictionary

    def with_trashed(self):
        self._with_trashed = True

        self._query = self._use_with_trashed(self._query)

        return self

    def _use_with_trashed(self, query):
        if self._with_trashed:
            return query.with_trashed()

        return query

    def _new_instance(self, model, related=None):
        return MorphTo(
            self.new_query(related),
            model,
            self._foreign_key,
            self._other_key if not related else related.get_key_name(),
            self._morph_type,
            self._relation,
        )

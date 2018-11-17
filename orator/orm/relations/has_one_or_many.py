# -*- coding: utf-8 -*-

from ..collection import Collection
from .relation import Relation
from .result import Result


class HasOneOrMany(Relation):
    def __init__(self, query, parent, foreign_key, local_key):
        """
        :type query: orator.orm.Builder

        :param parent: The parent model
        :type parent: Model

        :param foreign_key: The foreign key of the parent model
        :type foreign_key: str

        :param local_key: The local key of the parent model
        :type local_key: str
        """
        self._local_key = local_key
        self._foreign_key = foreign_key

        super(HasOneOrMany, self).__init__(query, parent)

    def add_constraints(self):
        """
        Set the base constraints of the relation query
        """
        if self._constraints:
            self._query.where(self._foreign_key, "=", self.get_parent_key())

    def add_eager_constraints(self, models):
        """
        Set the constraints for an eager load of the relation.

        :type models: list
        """
        return self._query.where_in(
            self._foreign_key, self.get_keys(models, self._local_key)
        )

    def match_one(self, models, results, relation):
        """
        Match the eargerly loaded resuls to their single parents.

        :param models: The parents
        :type models: list

        :param results: The results collection
        :type results: Collection

        :param relation: The relation
        :type relation: str

        :rtype: list
        """
        return self._match_one_or_many(models, results, relation, "one")

    def match_many(self, models, results, relation):
        """
        Match the eargerly loaded resuls to their single parents.

        :param models: The parents
        :type models: list

        :param results: The results collection
        :type results: Collection

        :param relation: The relation
        :type relation: str

        :rtype: list
        """
        return self._match_one_or_many(models, results, relation, "many")

    def _match_one_or_many(self, models, results, relation, type_):
        """
        Match the eargerly loaded resuls to their single parents.

        :param models: The parents
        :type models: list

        :param results: The results collection
        :type results: Collection

        :param relation: The relation
        :type relation: str

        :param type_: The match type
        :type type_: str

        :rtype: list
        """
        dictionary = self._build_dictionary(results)

        for model in models:
            key = model.get_attribute(self._local_key)

            if key in dictionary:
                value = Result(
                    self._get_relation_value(dictionary, key, type_), self, model
                )
            else:
                if type_ == "one":
                    value = Result(None, self, model)
                else:
                    value = Result(self._related.new_collection(), self, model)

            model.set_relation(relation, value)

        return models

    def _get_relation_value(self, dictionary, key, type):
        """
        Get the value of the relationship by one or many type.

        :type dictionary: dict
        :type key: str
        :type type: str
        """
        value = dictionary[key]

        if type == "one":
            return value[0]

        return self._related.new_collection(value)

    def _build_dictionary(self, results):
        """
        Build model dictionary keyed by the relation's foreign key.

        :param results: The results
        :type results: Collection

        :rtype: dict
        """
        dictionary = {}

        foreign = self.get_plain_foreign_key()

        for result in results:
            key = getattr(result, foreign)
            if key not in dictionary:
                dictionary[key] = []

            dictionary[key].append(result)

        return dictionary

    def save(self, model):
        """
        Attach a model instance to the parent models.

        :param model: The model instance to attach
        :type model: Model

        :rtype: Model
        """
        model.set_attribute(self.get_plain_foreign_key(), self.get_parent_key())

        if model.save():
            return model

        return False

    def save_many(self, models):
        """
        Attach a list of models to the parent instance.

        :param models: The models to attach
        :type models: list of Model

        :rtype: list
        """
        return list(map(self.save, models))

    def find_or_new(self, id, columns=None):
        """
        Find a model by its primary key or return new instance of the related model.

        :param id: The primary key
        :type id: mixed

        :param columns:  The columns to retrieve
        :type columns: list

        :rtype: Collection or Model
        """
        if columns is None:
            columns = ["*"]

        instance = self._query.find(id, columns)

        if instance is None:
            instance = self._related.new_instance()
            instance.set_attribute(self.get_plain_foreign_key(), self.get_parent_key())

        return instance

    def first_or_new(self, _attributes=None, **attributes):
        """
        Get the first related model record matching the attributes or instantiate it.

        :param attributes:  The attributes
        :type attributes: dict

        :rtype: Model
        """
        if _attributes is not None:
            attributes.update(_attributes)

        instance = self._query.where(attributes).first()

        if instance is None:
            instance = self._related.new_instance()
            instance.set_attribute(self.get_plain_foreign_key(), self.get_parent_key())

        return instance

    def first_or_create(self, _attributes=None, **attributes):
        """
        Get the first related record matching the attributes or create it.

        :param attributes:  The attributes
        :type attributes: dict

        :rtype: Model
        """
        if _attributes is not None:
            attributes.update(_attributes)

        instance = self._query.where(attributes).first()

        if instance is None:
            instance = self.create(**attributes)

        return instance

    def update_or_create(self, attributes, values=None):
        """
        Create or update a related record matching the attributes, and fill it with values.

        :param attributes: The attributes
        :type attributes: dict

        :param values: The values
        :type values: dict

        :rtype: Model
        """
        instance = self.first_or_new(**attributes)

        instance.fill(values)

        instance.save()

        return instance

    def create(self, _attributes=None, **attributes):
        """
        Create a new instance of the related model.

        :param attributes: The attributes
        :type attributes: dict

        :rtype: Model
        """
        if _attributes is not None:
            attributes.update(_attributes)

        instance = self._related.new_instance(attributes)

        instance.set_attribute(self.get_plain_foreign_key(), self.get_parent_key())

        instance.save()

        return instance

    def create_many(self, records):
        """
        Create a list of new instances of the related model.

        :param records: instances attributes
        :type records: list

        :rtype: list
        """
        instances = []

        for record in records:
            instances.append(self.create(**record))

        return instances

    def update(self, _attributes=None, **attributes):
        """
        Perform an update on all the related models.

        :param attributes: The attributes
        :type attributes: dict

        :rtype: int
        """
        if _attributes is not None:
            attributes.update(_attributes)

        if self._related.uses_timestamps():
            attributes[self.get_related_updated_at()] = self._related.fresh_timestamp()

        return self._query.update(attributes)

    def get_has_compare_key(self):
        return self.get_foreign_key()

    def get_foreign_key(self):
        return self._foreign_key

    def get_plain_foreign_key(self):
        segments = self.get_foreign_key().split(".")

        return segments[-1]

    def get_parent_key(self):
        return self._parent.get_attribute(self._local_key)

    def get_qualified_parent_key_name(self):
        return "%s.%s" % (self._parent.get_table(), self._local_key)

# -*- coding: utf-8 -*-

from .has_one_or_many import HasOneOrMany


class MorphOneOrMany(HasOneOrMany):

    def __init__(self, query, parent, morph_type, foreign_key, local_key):
        """
        :type query: orator.orm.Builder

        :param parent: The parent model
        :type parent: Model

        :param morph_type: The type of the morph
        :type morph_type: str

        :param foreign_key: The foreign key of the parent model
        :type foreign_key: str

        :param local_key: The local key of the parent model
        :type local_key: str
        """
        self._morph_type = morph_type
        self._morph_name = parent.get_morph_name()

        super(MorphOneOrMany, self).__init__(query, parent, foreign_key, local_key)

    def add_constraints(self):
        """
        Set the base constraints of the relation query
        """
        if self._constraints:
            super(MorphOneOrMany, self).add_constraints()

            self._query.where(self._morph_type, self._morph_name)

    def get_relation_count_query(self, query, parent):
        """
        Add the constraints for a relationship count query.

        :type query: Builder
        :type parent: Builder

        :rtype: Builder
        """
        query = super(MorphOneOrMany, self).get_relation_count_query(query, parent)

        return query.where(self._morph_type, self._morph_name)

    def add_eager_constraints(self, models):
        """
        Set the constraints for an eager load of the relation.

        :type models: list
        """
        super(MorphOneOrMany, self).add_eager_constraints(models)

        self._query.where(self._morph_type, self._morph_name)

    def save(self, model):
        """
        Attach a model instance to the parent models.

        :param model: The model instance to attach
        :type model: Model

        :rtype: Model
        """
        model.set_attribute(self.get_plain_morph_type(), self._morph_name)

        return super(MorphOneOrMany, self).save(model)

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
            columns = ['*']

        instance = self._query.find(id, columns)

        if instance is None:
            instance = self._related.new_instance()
            self._set_foreign_attributes_for_create(instance)

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
            self._set_foreign_attributes_for_create(instance)

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

        self._set_foreign_attributes_for_create(instance)

        instance.save()

        return instance

    def _set_foreign_attributes_for_create(self, model):
        """
        Set the foreign ID and type for creation a related model.
        """
        model.set_attribute(self.get_plain_foreign_key(), self.get_parent_key())

        model.set_attribute(self.get_plain_morph_type(), self._morph_name)

    def get_morph_type(self):
        return self._morph_type

    def get_plain_morph_type(self):
        return self._morph_type.split('.')[-1]

    def get_morph_name(self):
        return self._morph_name

    def _new_instance(self, parent):
        return self.__class__(
            self.new_query(),
            parent,
            self._morph_type,
            self._foreign_key,
            self._local_key
        )

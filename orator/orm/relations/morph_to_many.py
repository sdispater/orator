# -*- coding: utf-8 -*-

from .belongs_to_many import BelongsToMany


class MorphToMany(BelongsToMany):
    def __init__(
        self,
        query,
        parent,
        name,
        table,
        foreign_key,
        other_key,
        relation_name=None,
        inverse=False,
    ):
        """
        :param query: A Builder instance
        :type query: elquent.orm.Builder

        :param parent: The parent model
        :type parent: Model

        :param table: The pivot table
        :type table: str

        :param foreign_key: The foreign key
        :type foreign_key: str

        :param other_key: The other key
        :type other_key: str

        :param relation_name: The relation name
        :type relation_name: str

        :type inverse: bool
        """
        self._name = name
        self._inverse = inverse
        self._morph_type = name + "_type"
        self._morph_name = (
            query.get_model().get_morph_name() if inverse else parent.get_morph_name()
        )

        super(MorphToMany, self).__init__(
            query, parent, table, foreign_key, other_key, relation_name
        )

    def _set_where(self):
        """
        Set the where clause for the relation query.

        :return: self
        :rtype: BelongsToMany
        """
        super(MorphToMany, self)._set_where()

        self._query.where("%s.%s" % (self._table, self._morph_type), self._morph_name)

    def get_relation_count_query(self, query, parent):
        """
        Add the constraints for a relationship count query.

        :type query: orator.orm.Builder
        :type parent: orator.orm.Builder

        :rtype: orator.orm.Builder
        """
        query = super(MorphToMany, self).get_relation_count_query(query, parent)

        return query.where("%s.%s" % (self._table, self._morph_type), self._morph_name)

    def add_eager_constraints(self, models):
        """
        Set the constraints for an eager load of the relation.

        :type models: list
        """
        super(MorphToMany, self).add_eager_constraints(models)

        self._query.where("%s.%s" % (self._table, self._morph_type), self._morph_name)

    def _create_attach_record(self, id, timed):
        """
        Create a new pivot attachement record.
        """
        record = super(MorphToMany, self)._create_attach_record(id, timed)

        record[self._morph_type] = self._morph_name

        return record

    def _new_pivot_query(self):
        """
        Create a new query builder for the pivot table.

        :rtype: orator.orm.Builder
        """
        query = super(MorphToMany, self)._new_pivot_query()

        return query.where(self._morph_type, self._morph_name)

    def new_pivot(self, attributes=None, exists=False):
        """
        Create a new pivot model instance.
        """
        from .morph_pivot import MorphPivot

        pivot = MorphPivot(self._parent, attributes, self._table, exists)

        pivot.set_pivot_keys(self._foreign_key, self._other_key).set_morph_type(
            self._morph_type
        ).set_morph_name(self._morph_name)

        return pivot

    def get_morph_type(self):
        return self._morph_type

    def get_morph_name(self):
        return self._morph_name

    def _new_instance(self, model):
        return MorphToMany(
            self.new_query(),
            model,
            self._name,
            self._table,
            self._foreign_key,
            self._other_key,
            self._relation_name,
            self._inverse,
        )

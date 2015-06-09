# -*- coding: utf-8 -*-

from lazy_object_proxy import Proxy
from contextlib import contextmanager
from ...query.expression import QueryExpression
from ..collection import Collection


class RelationWrapper(object):

    def __init__(self, relationship):
        self._relationship = relationship

    def __dynamic(self, method):
        try:
            attribute = object.__getattribute__(self._relationship, method)
        except AttributeError:
            attribute = getattr(self._relationship.get_query(), method)

        def call(*args, **kwargs):
            result = attribute(*args, **kwargs)

            if result is self._relationship.get_query():
                return self

            if result is self._relationship:
                return self

            return result

        if not callable(attribute):
            return attribute

        return call

    def __getattr__(self, item):
        return self.__dynamic(item)


class Relation(Proxy):

    _constraints = True
    _query = None
    _parent = None
    _related = None

    def __init__(self, query, parent):
        """
        :param query: A Builder instance
        :type query: orm.orator.Builder

        :param parent: The parent model
        :type parent: Model
        """
        super(Relation, self).__init__(self.get_results)

        self._query = query
        self._parent = parent
        self._related = query.get_model()

        self.add_constraints()

    def add_constraints(self):
        """
        Set the base constraints on the relation query.

        :rtype: None
        """
        raise NotImplementedError

    def add_eager_constraints(self, models):
        """
        Set the constraints for an eager load of the relation.

        :type models: list
        """
        raise NotImplementedError

    def init_relation(self, models, relation):
        """
        Initialize the relation on a set of models.

        :type models: list
        :type relation:  str
        """
        raise NotImplementedError

    def match(self, models, results, relation):
        """
        Match the eagerly loaded results to their parents.

        :type models: list
        :type results: Collection
        :type relation:  str
        """
        raise NotImplementedError

    def get_results(self):
        """
        Get the results of the relationship.
        """
        raise NotImplementedError

    def refresh(self):
        del self.__wrapped__

        return self

    def set_results(self, results):
        self.__wrapped__ = results

        return self

    def get_eager(self):
        """
        Get the relationship for eager loading.

        :rtype: Collection
        """
        try:
            return object.__getattribute__(self, 'get')()
        except AttributeError:
            return self._query.get()

    def touch(self):
        """
        Touch all of the related models for the relationship.
        """
        column = self.get_related().get_updated_at_column()

        self.raw_update({column: self.get_related().fresh_timestamp()})

    def raw_update(self, attributes=None):
        """
        Run a raw update against the base query.

        :type attributes: dict

        :rtype: int
        """
        if attributes is None:
            attributes = {}

        return self._query.update(attributes)

    def get_relation_count_query(self, query, parent):
        """
        Add the constraints for a relationship count query.

        :type query: Builder
        :type parent: Builder

        :rtype: Builder
        """
        query.select(QueryExpression('COUNT(*)'))

        key = self.wrap(self.get_qualified_parent_key_name())

        return query.where(self.get_has_compare_key(), '=', QueryExpression(key))

    @classmethod
    @contextmanager
    def no_constraints(cls, with_subclasses=False):
        """
        Runs a callback with constraints disabled on the relation.
        """
        cls._constraints = False

        if with_subclasses:
            for klass in cls.__subclasses__():
                klass._constraints = False

        try:
            yield cls
        except Exception:
            raise
        finally:
            cls._constraints = True
            if with_subclasses:
                for klass in cls.__subclasses__():
                    klass._constraints = True

    def get_keys(self, models, key=None):
        """
        Get all the primary keys for an array of models.

        :type models: list
        :type key: str

        :rtype: list
        """
        return list(set(map(lambda value: value.get_attribute(key) if key else value.get_key(), models)))

    def get_query(self):
        return self._query

    def get_base_query(self):
        return self._query.get_query()

    def merge_query(self, query):
        self._query.merge_wheres(query.wheres, query.get_query().get_raw_bindings()['where'])

    def get_parent(self):
        return self._parent

    def get_qualified_parent_key_name(self):
        return self._parent.get_qualified_key_name()

    def get_related(self):
        return self._related

    def created_at(self):
        """
        Get the name of the "created at" column.

        :rtype: str
        """
        return self._parent.get_created_at_column()

    def updated_at(self):
        """
        Get the name of the "updated at" column.

        :rtype: str
        """
        return self._parent.get_updated_at_column()

    def get_related_updated_at(self):
        """
        Get the name of the related model's "updated at" column.

        :rtype: str
        """
        return self._related.get_updated_at_column()

    def wrap(self, value):
        """
        Wrap the given calue with the parent's query grammar.

        :rtype: str
        """
        return self._parent.new_query().get_query().get_grammar().wrap(value)

    def set_parent(self, parent):
        self._parent = parent

    def __call__(self, *args, **kwargs):
        relation = self.new_instance(self._parent)

        return RelationWrapper(relation)

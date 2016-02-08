# -*- coding: utf-8 -*-

import types
from functools import update_wrapper
from .relations.wrapper import Wrapper
from .builder import Builder
from ..query import QueryBuilder
from .relations import (
    HasOne, HasMany, HasManyThrough,
    BelongsTo, BelongsToMany,
    MorphOne, MorphMany, MorphTo, MorphToMany
)


class accessor(object):

    def __init__(self, accessor_, attribute=None):
        self.accessor = accessor_
        self.mutator_ = None
        if attribute is not None:
            self.attribute = attribute
        else:
            if isinstance(accessor_, property):
                self.attribute = accessor_.fget.__name__
            else:
                self.attribute = self.accessor.__name__

        self.expr = accessor_
        if accessor_ is not None:
            update_wrapper(self, accessor_)

    def __get__(self, instance, owner):
        if instance is None:
            return self.expr
        else:
            return self.accessor(instance)

    def __set__(self, instance, value):
        if self.mutator_ is None:
            return instance.set_attribute(self.attribute, value)

        self.mutator_(instance, value)

    def mutator(self, f):
        self.mutator_ = f

        return mutator(f, self.attribute)


class mutator(object):

    def __init__(self, mutator_, attribute=None):
        self.mutator = mutator_
        self.accessor_ = None
        self.attribute = attribute or self.mutator.__name__

    def __get__(self, instance, owner):
        if instance is None:
            return self.mutator
        else:
            if self.accessor_ is None:
                return instance.get_attribute(self.attribute)

            return self.accessor_(instance)

    def __set__(self, instance, value):
        self.mutator(instance, value)

    def accessor(self, f):
        self.accessor_ = f

        return accessor(f, self.attribute)


class column(object):

    def __init__(self, property_, attribute=None):
        self.property = property_
        self.mutator_ = None
        self.accessor_ = None
        if attribute is not None:
            self.attribute = attribute
        else:
            if isinstance(property_, property):
                self.attribute = property_.fget.__name__
            else:
                self.attribute = self.property.__name__

    def __get__(self, instance, owner):
        if instance is None:
            return self.mutator_
        else:
            if self.accessor_ is None:
                return instance.get_attribute(self.attribute)

            return self.accessor_(instance)

    def __set__(self, instance, value):
        if self.mutator_ is None:
            return instance.set_attribute(self.attribute, value)

        self.mutator_(instance, value)

    def mutator(self, f):
        self.mutator_ = f

        return mutator(f, self.attribute)

    def accessor(self, f):
        self.accessor_ = f

        return accessor(f, self.attribute)


class scope(classmethod):
    """
    Decorator to add local scopes.
    """

    def __init__(self, method):
        super(scope, self).__init__(method)

        self._method = method
        self._owner = None

        update_wrapper(self, method)

    def __get__(self, instance, owner, *args, **kwargs):
        if instance:
            self._owner = None
        else:
            self._owner = owner

        return self

    def __call__(self, *args, **kwargs):
        if not self._owner:
            return self._method(self._owner, *args, **kwargs)
        else:
            return getattr(self._owner.query(), self._method.__name__)(*args, **kwargs)


# Relations decorators
class relation(object):
    """
    Base relation decorator
    """

    relation_class = None

    def __init__(self, func=None, relation=None):
        self._relation = relation
        self._related = None
        self._conditions = None

        self.set_func(func)

    def set_func(self, func):
        self.func = func

        if self._relation is None:
            if isinstance(func, property):
                self._relation = func.fget.__name__ if func else None
            else:
                self._relation = func.__name__ if func else None

        self.expr = func
        if func is not None:
            update_wrapper(self, func)

    def __get__(self, instance, owner):
        if instance is None:
            return self.expr

        if self._relation in instance._relations:
            return instance._relations[self._relation]

        self._related = self.func(instance)
        if isinstance(self._related, (Builder, QueryBuilder)):
            # Extra conditions on relation
            self._conditions = self._related
            self._related = self._related.get_model().__class__

        relation = self._get(instance)

        if self._conditions:
            # Setting extra conditions
            self._set_conditions(relation)

        relation = Wrapper(relation)

        instance._relations[self._relation] = relation

        return relation

    def _get(self, instance):
        raise NotImplementedError()

    def _set_conditions(self, relation):
        relation.merge_query(self._conditions)
        relation.set_extra_query(self._conditions)

    def __call__(self, func):
        self.set_func(func)

        return self


class has_one(relation):
    """
    Has One relationship decorator
    """

    relation_class = HasOne

    def __init__(self, foreign_key=None, local_key=None, relation=None):
        if isinstance(foreign_key, (types.FunctionType, types.MethodType)):
            func = foreign_key
            foreign_key = None
        else:
            func = None

        self._foreign_key = foreign_key
        self._local_key = local_key

        super(has_one, self).__init__(func, relation)

    def _get(self, instance):
        return instance.has_one(
            self._related,
            self._foreign_key,
            self._local_key,
            self._relation,
            _wrapped=False
        )


class morph_one(relation):
    """
    Morph One relationship decorator
    """

    relation_class = MorphOne

    def __init__(self, name, type_column=None, id_column=None, local_key=None, relation=None):
        if isinstance(name, (types.FunctionType, types.MethodType)):
            raise RuntimeError('morph_one relation requires a name')

        self._name = name
        self._type_column = type_column
        self._id_column = id_column
        self._local_key = local_key

        super(morph_one, self).__init__(relation=relation)

    def _get(self, instance):
        return instance.morph_one(
            self._related, self._name,
            self._type_column, self._id_column,
            self._local_key, self._relation,
            _wrapped=False
        )


class belongs_to(relation):
    """
    Belongs to relationship decorator
    """

    relation_class = BelongsTo

    def __init__(self, foreign_key=None, other_key=None, relation=None):
        if isinstance(foreign_key, (types.FunctionType, types.MethodType)):
            func = foreign_key
            foreign_key = None
        else:
            func = None

        self._foreign_key = foreign_key
        self._other_key = other_key

        super(belongs_to, self).__init__(func, relation)

    def _get(self, instance):
        return instance.belongs_to(
            self._related,
            self._foreign_key,
            self._other_key,
            self._relation,
            _wrapped=False
        )

    def _set(self, relation):
        relation._foreign_key = self._foreign_key
        relation._other_key = self._other_key
        relation._relation = self._relation


class morph_to(relation):
    """
    Morph To relationship decorator
    """

    relation_class = MorphTo

    def __init__(self, name=None, type_column=None, id_column=None):
        if isinstance(name, (types.FunctionType, types.MethodType)):
            func = name
            name = None
        else:
            func = None

        self._name = name
        self._type_column = type_column
        self._id_column = id_column

        super(morph_to, self).__init__(func, name)

    def _get(self, instance):
        return instance.morph_to(
            self._relation,
            self._type_column, self._id_column,
            _wrapped=False
        )


class has_many(relation):
    """
    Has Many relationship decorator
    """

    relation_class = HasMany

    def __init__(self, foreign_key=None, local_key=None, relation=None):
        if isinstance(foreign_key, (types.FunctionType, types.MethodType)):
            func = foreign_key
            foreign_key = None
        else:
            func = None

        self._foreign_key = foreign_key
        self._local_key = local_key

        super(has_many, self).__init__(func, relation)

    def _get(self, instance):
        return instance.has_many(
            self._related,
            self._foreign_key,
            self._local_key,
            self._relation,
            _wrapped=False
        )


class has_many_through(relation):
    """
    Has Many Through relationship decorator
    """

    relation_class = HasManyThrough

    def __init__(self, through, first_key=None, second_key=None, relation=None):
        if isinstance(through, (types.FunctionType, types.MethodType)):
            raise RuntimeError('has_many_through relation requires the through parameter')

        self._through = through
        self._first_key = first_key
        self._second_key = second_key

        super(has_many_through, self).__init__(relation=relation)

    def _get(self, instance):
        return instance.has_many_through(
            self._related,
            self._through,
            self._first_key,
            self._second_key,
            self._relation,
            _wrapped=False
        )


class morph_many(relation):
    """
    Morph Many relationship decorator
    """

    relation_class = MorphMany

    def __init__(self, name, type_column=None, id_column=None, local_key=None, relation=None):
        if isinstance(name, (types.FunctionType, types.MethodType)):
            raise RuntimeError('morph_many relation requires a name')

        self._name = name
        self._type_column = type_column
        self._id_column = id_column
        self._local_key = local_key

        super(morph_many, self).__init__(relation=relation)

    def _get(self, instance):
        return instance.morph_many(
            self._related, self._name,
            self._type_column, self._id_column,
            self._local_key, self._relation,
            _wrapped=False
        )


class belongs_to_many(relation):
    """
    Belongs To Many relationship decorator
    """

    relation_class = BelongsToMany

    def __init__(self, table=None, foreign_key=None, other_key=None,
                 relation=None, with_timestamps=False, with_pivot=None):
        if isinstance(table, (types.FunctionType, types.MethodType)):
            func = table
            table = None
        else:
            func = None

        self._table = table
        self._foreign_key = foreign_key
        self._other_key = other_key

        self._timestamps = with_timestamps
        self._pivot = with_pivot

        super(belongs_to_many, self).__init__(func, relation)

    def _get(self, instance):
        r = instance.belongs_to_many(
            self._related,
            self._table,
            self._foreign_key,
            self._other_key,
            self._relation,
            _wrapped=False
        )

        if self._timestamps:
            r = r.with_timestamps()

        if self._pivot:
            r = r.with_pivot(*self._pivot)

        return r


class morph_to_many(relation):
    """
    Morph To Many relationship decorator
    """

    relation_class = MorphToMany

    def __init__(self, name, table=None, foreign_key=None, other_key=None, relation=None):
        if isinstance(name, (types.FunctionType, types.MethodType)):
            raise RuntimeError('morph_to_many relation required a name')

        self._name = name
        self._table = table
        self._foreign_key = foreign_key
        self._other_key = other_key

        super(morph_to_many, self).__init__(relation=relation)

    def _get(self, instance):
        return instance.morph_to_many(
            self._related,
            self._name,
            self._table,
            self._foreign_key,
            self._other_key,
            relation=self._relation,
            _wrapped=False
        )


class morphed_by_many(relation):
    """
    Morphed By Many relationship decorator
    """

    relation_class = MorphToMany

    def __init__(self, name, table=None, foreign_key=None, other_key=None, relation=None):
        if isinstance(foreign_key, (types.FunctionType, types.MethodType)):
            raise RuntimeError('morphed_by_many relation requires a name')

        self._name = name
        self._table = table
        self._foreign_key = foreign_key
        self._other_key = other_key

        super(morphed_by_many, self).__init__(relation=relation)

    def _get(self, instance):
        return instance.morphed_by_many(
            self._related,
            self._name,
            self._table,
            self._foreign_key,
            self._other_key,
            self._relation,
            _wrapped=False
        )

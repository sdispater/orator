# -*- coding: utf-8 -*-

from functools import update_wrapper


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

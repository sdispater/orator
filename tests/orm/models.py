import hashlib
import json

from flexmock import flexmock
from orator.orm import Model
from orator.orm.builder import Builder
from orator.orm.utils import mutator, accessor
from orator.query.builder import QueryBuilder


class OrmModelStub(Model):

    __table__ = "stub"

    __guarded__ = []

    @accessor
    def list_items(self):
        return json.loads(self.get_raw_attribute("list_items"))

    @list_items.mutator
    def set_list_items(self, value):
        self.set_raw_attribute("list_items", json.dumps(value))

    @mutator
    def password(self, value):
        self.set_raw_attribute("password_hash", hashlib.md5(value.encode()).hexdigest())

    @password.accessor
    def get_password(self):
        return "******"

    @accessor
    def appendable(self):
        return "appended"

    def public_increment(self, column, amount=1):
        return self._increment(column, amount)

    def get_dates(self):
        return []


class OrmModelHydrateRawStub(Model):
    @classmethod
    def hydrate(cls, items, connection=None):
        return "hydrated"


class OrmModelWithStub(Model):
    def new_query(self):
        mock = flexmock(Builder(None))
        mock.should_receive("with_").once().with_args("foo", "bar").and_return("foo")

        return mock


class OrmModelSaveStub(Model):

    __table__ = "save_stub"

    __guarded__ = []

    def save(self, options=None):
        self.__saved = True

    def set_incrementing(self, value):
        self.__incrementing__ = value

    def get_saved(self):
        return self.__saved


class OrmModelFindStub(Model):
    def new_query(self):
        flexmock(Builder).should_receive("find").once().with_args(1, ["*"]).and_return(
            "foo"
        )

        return Builder(None)


class OrmModelFindWithWriteConnectionStub(Model):
    def new_query(self):
        mock = flexmock(Builder)
        mock_query = flexmock(QueryBuilder)
        mock_query.should_receive("use_write_connection").once().and_return(flexmock)
        mock.should_receive("find").once().with_args(1).and_return("foo")

        return Builder(QueryBuilder(None, None, None))


class OrmModelFindManyStub(Model):
    def new_query(self):
        mock = flexmock(Builder)
        mock.should_receive("find").once().with_args([1, 2], ["*"]).and_return("foo")

        return Builder(QueryBuilder(None, None, None))


class OrmModelDestroyStub(Model):
    def new_query(self):
        mock = flexmock(Builder)
        model = flexmock()
        mock_query = flexmock(QueryBuilder)
        mock_query.should_receive("where_in").once().with_args(
            "id", [1, 2, 3]
        ).and_return(flexmock)
        mock.should_receive("get").once().and_return([model])
        model.should_receive("delete").once()

        return Builder(QueryBuilder(None, None, None))


class OrmModelNoTableStub(Model):

    pass


class OrmModelCastingStub(Model):

    __casts__ = {
        "first": "int",
        "second": "float",
        "third": "str",
        "fourth": "bool",
        "fifth": "boolean",
        "sixth": "dict",
        "seventh": "list",
        "eighth": "json",
    }


class OrmModelCreatedAt(Model):

    __timestamps__ = ["created_at"]


class OrmModelUpdatedAt(Model):

    __timestamps__ = ["updated_at"]


class OrmModelDefaultAttributes(Model):

    __attributes__ = {"foo": "bar"}

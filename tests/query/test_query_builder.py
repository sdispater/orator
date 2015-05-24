# -*- coding: utf-8 -*-

import re

from .. import OratorTestCase
from .. import mock

from ..utils import MockConnection, MockProcessor

from orator.query.grammars import (
    QueryGrammar,
    PostgresQueryGrammar,
    SQLiteQueryGrammar,
    MySqlQueryGrammar
)
from orator.query.builder import QueryBuilder
from orator.query.expression import QueryExpression
from orator.query.join_clause import JoinClause


class QueryBuilderTestCase(OratorTestCase):

    def test_basic_select(self):
        builder = self.get_builder()
        builder.select('*').from_('users')

        self.assertEqual('SELECT * FROM "users"', builder.to_sql())

    def test_basic_select_use_write_connection(self):
        builder = self.get_builder()
        builder.use_write_connection().select('*').from_('users').get()
        builder.get_connection().select.assert_called_once_with(
            'SELECT * FROM "users"',
            [],
            False
        )

        builder = self.get_builder()
        builder.select('*').from_('users').get()
        builder.get_connection().select.assert_called_once_with(
            'SELECT * FROM "users"',
            [],
            True
        )

    def test_alias_wrapping_as_whole_constant(self):
        builder = self.get_builder()
        builder.select('x.y as foo.bar').from_('baz')

        self.assertEqual(
            'SELECT "x"."y" AS "foo.bar" FROM "baz"',
            builder.to_sql()
        )

    def test_adding_selects(self):
        builder = self.get_builder()
        builder.select('foo').add_select('bar').add_select('baz', 'boom').from_('users')

        self.assertEqual(
            'SELECT "foo", "bar", "baz", "boom" FROM "users"',
            builder.to_sql()
        )

    def test_basic_select_with_prefix(self):
        builder = self.get_builder()
        builder.get_grammar().set_table_prefix('prefix_')
        builder.select('*').from_('users')

        self.assertEqual(
            'SELECT * FROM "prefix_users"',
            builder.to_sql()
        )

    def test_basic_select_distinct(self):
        builder = self.get_builder()
        builder.distinct().select('foo', 'bar').from_('users')

        self.assertEqual(
            'SELECT DISTINCT "foo", "bar" FROM "users"',
            builder.to_sql()
        )

    def test_basic_alias(self):
        builder = self.get_builder()
        builder.select('foo as bar').from_('users')

        self.assertEqual(
            'SELECT "foo" AS "bar" FROM "users"',
            builder.to_sql()
        )

    def test_mysql_wrapping_protects_qutotation_marks(self):
        builder = self.get_mysql_builder()
        builder.select('*').from_('some`table')

        self.assertEqual(
            'SELECT * FROM `some``table`',
            builder.to_sql()
        )

    def test_where_day_mysql(self):
        builder = self.get_mysql_builder()
        builder.select('*').from_('users').where_day('created_at', '=', 1)

        self.assertEqual(
            'SELECT * FROM `users` WHERE DAY(`created_at`) = %s',
            builder.to_sql()
        )
        self.assertEqual([1], builder.get_bindings())

    def test_where_month_mysql(self):
        builder = self.get_mysql_builder()
        builder.select('*').from_('users').where_month('created_at', '=', 5)

        self.assertEqual(
            'SELECT * FROM `users` WHERE MONTH(`created_at`) = %s',
            builder.to_sql()
        )
        self.assertEqual([5], builder.get_bindings())

    def test_where_year_mysql(self):
        builder = self.get_mysql_builder()
        builder.select('*').from_('users').where_year('created_at', '=', 2014)

        self.assertEqual(
            'SELECT * FROM `users` WHERE YEAR(`created_at`) = %s',
            builder.to_sql()
        )
        self.assertEqual([2014], builder.get_bindings())

    def test_where_day_postgres(self):
        builder = self.get_postgres_builder()
        builder.select('*').from_('users').where_day('created_at', '=', 1)

        self.assertEqual(
            'SELECT * FROM "users" WHERE DAY("created_at") = %s',
            builder.to_sql()
        )
        self.assertEqual([1], builder.get_bindings())

    def test_where_month_postgres(self):
        builder = self.get_postgres_builder()
        builder.select('*').from_('users').where_month('created_at', '=', 5)

        self.assertEqual(
            'SELECT * FROM "users" WHERE MONTH("created_at") = %s',
            builder.to_sql()
        )
        self.assertEqual([5], builder.get_bindings())

    def test_where_year_postgres(self):
        builder = self.get_postgres_builder()
        builder.select('*').from_('users').where_year('created_at', '=', 2014)

        self.assertEqual(
            'SELECT * FROM "users" WHERE YEAR("created_at") = %s',
            builder.to_sql()
        )
        self.assertEqual([2014], builder.get_bindings())

    def test_where_day_sqlite(self):
        builder = self.get_sqlite_builder()
        builder.select('*').from_('users').where_day('created_at', '=', 1)

        self.assertEqual(
            'SELECT * FROM "users" WHERE strftime(\'%d\', "created_at") = ?',
            builder.to_sql()
        )
        self.assertEqual([1], builder.get_bindings())

    def test_where_month_sqlite(self):
        builder = self.get_sqlite_builder()
        builder.select('*').from_('users').where_month('created_at', '=', 5)

        self.assertEqual(
            'SELECT * FROM "users" WHERE strftime(\'%m\', "created_at") = ?',
            builder.to_sql()
        )
        self.assertEqual([5], builder.get_bindings())

    def test_where_year_sqlite(self):
        builder = self.get_sqlite_builder()
        builder.select('*').from_('users').where_year('created_at', '=', 2014)

        self.assertEqual(
            'SELECT * FROM "users" WHERE strftime(\'%Y\', "created_at") = ?',
            builder.to_sql()
        )
        self.assertEqual([2014], builder.get_bindings())

    def test_where_between(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where_between('id', [1, 2])
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" BETWEEN ? AND ?',
            builder.to_sql()
        )
        self.assertEqual([1, 2], builder.get_bindings())

        builder = self.get_builder()
        builder.select('*').from_('users').where_not_between('id', [1, 2])
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" NOT BETWEEN ? AND ?',
            builder.to_sql()
        )
        self.assertEqual([1, 2], builder.get_bindings())

    def test_basic_or_where(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where('id', '=', 1).or_where('email', '=', 'foo')
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" = ? OR "email" = ?',
            builder.to_sql()
        )
        self.assertEqual([1, 'foo'], builder.get_bindings())

    def test_raw_wheres(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where_raw('id = ? or email = ?', [1, 'foo'])
        self.assertEqual(
            'SELECT * FROM "users" WHERE id = ? OR email = ?',
            builder.to_sql()
        )
        self.assertEqual([1, 'foo'], builder.get_bindings())

        builder = self.get_builder()
        builder.select('*').from_('users').where_raw('id = ?', [1])
        self.assertEqual(
            'SELECT * FROM "users" WHERE id = ?',
            builder.to_sql()
        )
        self.assertEqual([1], builder.get_bindings())

    def test_raw_or_wheres(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where('id', '=', 1).or_where_raw('email = ?', ['foo'])
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" = ? OR email = ?',
            builder.to_sql()
        )
        self.assertEqual([1, 'foo'], builder.get_bindings())

    def test_basic_where_ins(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where_in('id', [1, 2, 3])
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" IN (?, ?, ?)',
            builder.to_sql()
        )
        self.assertEqual([1, 2, 3], builder.get_bindings())

        builder = self.get_builder()
        builder.select('*').from_('users').where('id', '=', 1).or_where_in('id', [1, 2, 3])
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" = ? OR "id" IN (?, ?, ?)',
            builder.to_sql()
        )
        self.assertEqual([1, 1, 2, 3], builder.get_bindings())

    def test_basic_where_not_ins(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where_not_in('id', [1, 2, 3])
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" NOT IN (?, ?, ?)',
            builder.to_sql()
        )
        self.assertEqual([1, 2, 3], builder.get_bindings())

        builder = self.get_builder()
        builder.select('*').from_('users').where('id', '=', 1).or_where_not_in('id', [1, 2, 3])
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" = ? OR "id" NOT IN (?, ?, ?)',
            builder.to_sql()
        )
        self.assertEqual([1, 1, 2, 3], builder.get_bindings())

    def test_empty_where_ins(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where_in('id', [])
        self.assertEqual(
            'SELECT * FROM "users" WHERE 0 = 1',
            builder.to_sql()
        )
        self.assertEqual([], builder.get_bindings())

        builder = self.get_builder()
        builder.select('*').from_('users').where('id', '=', 1).or_where_in('id', [])
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" = ? OR 0 = 1',
            builder.to_sql()
        )
        self.assertEqual([1], builder.get_bindings())

    def test_empty_where_not_ins(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where_not_in('id', [])
        self.assertEqual(
            'SELECT * FROM "users" WHERE 1 = 1',
            builder.to_sql()
        )
        self.assertEqual([], builder.get_bindings())

        builder = self.get_builder()
        builder.select('*').from_('users').where('id', '=', 1).or_where_not_in('id', [])
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" = ? OR 1 = 1',
            builder.to_sql()
        )
        self.assertEqual([1], builder.get_bindings())

    def test_unions(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where('id', '=', 1)
        builder.union(self.get_builder().select('*').from_('users').where('id', '=', 2))
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" = ? UNION SELECT * FROM "users" WHERE "id" = ?',
            builder.to_sql()
        )
        self.assertEqual([1, 2], builder.get_bindings())

        builder = self.get_mysql_builder()
        builder.select('*').from_('users').where('id', '=', 1)
        builder.union(self.get_mysql_builder().select('*').from_('users').where('id', '=', 2))
        self.assertEqual(
            '(SELECT * FROM `users` WHERE `id` = %s) UNION (SELECT * FROM `users` WHERE `id` = %s)',
            builder.to_sql()
        )
        self.assertEqual([1, 2], builder.get_bindings())

    def test_union_alls(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where('id', '=', 1)
        builder.union_all(self.get_builder().select('*').from_('users').where('id', '=', 2))
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" = ? UNION ALL SELECT * FROM "users" WHERE "id" = ?',
            builder.to_sql()
        )
        self.assertEqual([1, 2], builder.get_bindings())

    def test_multiple_unions(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where('id', '=', 1)
        builder.union(self.get_builder().select('*').from_('users').where('id', '=', 2))
        builder.union(self.get_builder().select('*').from_('users').where('id', '=', 3))
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" = ? '
            'UNION SELECT * FROM "users" WHERE "id" = ? '
            'UNION SELECT * FROM "users" WHERE "id" = ?',
            builder.to_sql()
        )
        self.assertEqual([1, 2, 3], builder.get_bindings())

    def test_multiple_union_alls(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where('id', '=', 1)
        builder.union_all(self.get_builder().select('*').from_('users').where('id', '=', 2))
        builder.union_all(self.get_builder().select('*').from_('users').where('id', '=', 3))
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" = ? '
            'UNION ALL SELECT * FROM "users" WHERE "id" = ? '
            'UNION ALL SELECT * FROM "users" WHERE "id" = ?',
            builder.to_sql()
        )
        self.assertEqual([1, 2, 3], builder.get_bindings())

    def test_union_order_bys(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where('id', '=', 1)
        builder.union(self.get_builder().select('*').from_('users').where('id', '=', 2))
        builder.order_by('id', 'desc')
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" = ? '
            'UNION SELECT * FROM "users" WHERE "id" = ? '
            'ORDER BY "id" DESC',
            builder.to_sql()
        )
        self.assertEqual([1, 2], builder.get_bindings())

    def test_union_limits_and_offsets(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where('id', '=', 1)
        builder.union(self.get_builder().select('*').from_('users').where('id', '=', 2))
        builder.skip(5).take(10)
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" = ? '
            'UNION SELECT * FROM "users" WHERE "id" = ? '
            'LIMIT 10 OFFSET 5',
            builder.to_sql()
        )
        self.assertEqual([1, 2], builder.get_bindings())

    def test_mysql_union_order_bys(self):
        builder = self.get_mysql_builder()
        builder.select('*').from_('users').where('id', '=', 1)
        builder.union(self.get_mysql_builder().select('*').from_('users').where('id', '=', 2))
        builder.order_by('id', 'desc')
        self.assertEqual(
            '(SELECT * FROM `users` WHERE `id` = %s) '
            'UNION (SELECT * FROM `users` WHERE `id` = %s) '
            'ORDER BY `id` DESC',
            builder.to_sql()
        )
        self.assertEqual([1, 2], builder.get_bindings())

    def test_mysql_union_limits_and_offsets(self):
        builder = self.get_mysql_builder()
        builder.select('*').from_('users').where('id', '=', 1)
        builder.union(self.get_mysql_builder().select('*').from_('users').where('id', '=', 2))
        builder.skip(5).take(10)
        self.assertEqual(
            '(SELECT * FROM `users` WHERE `id` = %s) '
            'UNION (SELECT * FROM `users` WHERE `id` = %s) '
            'LIMIT 10 OFFSET 5',
            builder.to_sql()
        )
        self.assertEqual([1, 2], builder.get_bindings())

    def test_sub_select_where_in(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where_in(
            'id',
            self.get_builder().select('id').from_('users').where('age', '>', 25).take(3)
        )
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" IN (SELECT "id" FROM "users" WHERE "age" > ? LIMIT 3)',
            builder.to_sql()
        )
        self.assertEqual([25], builder.get_bindings())

        builder = self.get_builder()
        builder.select('*').from_('users').where_not_in(
            'id',
            self.get_builder().select('id').from_('users').where('age', '>', 25).take(3)
        )
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" NOT IN (SELECT "id" FROM "users" WHERE "age" > ? LIMIT 3)',
            builder.to_sql()
        )
        self.assertEqual([25], builder.get_bindings())

    def test_basic_where_null(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where_null('id')
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" IS NULL',
            builder.to_sql()
        )
        self.assertEqual([], builder.get_bindings())

        builder = self.get_builder()
        builder.select('*').from_('users').where('id', '=', 1).or_where_null('id')
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" = ? OR "id" IS NULL',
            builder.to_sql()
        )
        self.assertEqual([1], builder.get_bindings())

    def test_basic_where_not_null(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where_not_null('id')
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" IS NOT NULL',
            builder.to_sql()
        )
        self.assertEqual([], builder.get_bindings())

        builder = self.get_builder()
        builder.select('*').from_('users').where('id', '=', 1).or_where_not_null('id')
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" = ? OR "id" IS NOT NULL',
            builder.to_sql()
        )
        self.assertEqual([1], builder.get_bindings())

    def test_group_bys(self):
        builder = self.get_builder()
        builder.select('*').from_('users').group_by('id', 'email')
        self.assertEqual(
            'SELECT * FROM "users" GROUP BY "id", "email"',
            builder.to_sql()
        )

    def test_order_bys(self):
        builder = self.get_builder()
        builder.select('*').from_('users').order_by('email').order_by('age', 'desc')
        self.assertEqual(
            'SELECT * FROM "users" ORDER BY "email" ASC, "age" DESC',
            builder.to_sql()
        )

        builder = self.get_builder()
        builder.select('*').from_('users').order_by('email').order_by_raw('"age" ? desc', ['foo'])
        self.assertEqual(
            'SELECT * FROM "users" ORDER BY "email" ASC, "age" ? DESC',
            builder.to_sql()
        )

    def test_havings(self):
        builder = self.get_builder()
        builder.select('*').from_('users').having('email', '>', 1)
        self.assertEqual(
            'SELECT * FROM "users" HAVING "email" > ?',
            builder.to_sql()
        )
        self.assertEqual([1], builder.get_bindings())

        builder = self.get_builder()
        builder.select('*').from_('users')\
            .or_having('email', '=', 'foo@bar.com')\
            .or_having('email', '=', 'foo2@bar.com')
        self.assertEqual(
            'SELECT * FROM "users" HAVING "email" = ? OR "email" = ?',
            builder.to_sql()
        )
        self.assertEqual(['foo@bar.com', 'foo2@bar.com'], builder.get_bindings())

        builder = self.get_builder()
        builder.select('*').from_('users')\
            .group_by('email')\
            .having('email', '>', 1)
        self.assertEqual(
            'SELECT * FROM "users" GROUP BY "email" HAVING "email" > ?',
            builder.to_sql()
        )
        self.assertEqual([1], builder.get_bindings())

        builder = self.get_builder()
        builder.select('email as foo_mail').from_('users')\
            .having('foo_mail', '>', 1)
        self.assertEqual(
            'SELECT "email" AS "foo_mail" FROM "users" HAVING "foo_mail" > ?',
            builder.to_sql()
        )
        self.assertEqual([1], builder.get_bindings())

        builder = self.get_builder()
        builder.select('category', QueryExpression('count(*) as "total"'))\
            .from_('item')\
            .where('department', '=', 'popular')\
            .group_by('category')\
            .having('total', '>', QueryExpression('3'))
        self.assertEqual(
            'SELECT "category", count(*) as "total" '
            'FROM "item" '
            'WHERE "department" = ? '
            'GROUP BY "category" '
            'HAVING "total" > 3',
            builder.to_sql()
        )
        self.assertEqual(['popular'], builder.get_bindings())

        builder = self.get_builder()
        builder.select('category', QueryExpression('count(*) as "total"'))\
            .from_('item')\
            .where('department', '=', 'popular')\
            .group_by('category')\
            .having('total', '>', 3)
        self.assertEqual(
            'SELECT "category", count(*) as "total" '
            'FROM "item" '
            'WHERE "department" = ? '
            'GROUP BY "category" '
            'HAVING "total" > ?',
            builder.to_sql()
        )
        self.assertEqual(['popular', 3], builder.get_bindings())

    def test_having_followed_by_select_get(self):
        builder = self.get_builder()
        query = 'SELECT "category", count(*) as "total" ' \
                'FROM "item" ' \
                'WHERE "department" = ? ' \
                'GROUP BY "category" ' \
                'HAVING "total" > ?'
        results = {
            'category': 'rock',
            'total': 5
        }
        builder.get_connection().select.return_value = results
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results: results)
        result = builder.select('category', QueryExpression('count(*) as "total"'))\
            .from_('item')\
            .where('department', '=', 'popular')\
            .group_by('category')\
            .having('total', '>', 3)\
            .get()

        builder.get_connection().select.assert_called_once_with(
            query,
            ['popular', 3],
            True
        )
        builder.get_processor().process_select.assert_called_once_with(
            builder,
            results
        )
        self.assertEqual(results, result)
        self.assertEqual(['popular', 3], builder.get_bindings())

        # Using raw value
        builder = self.get_builder()
        query = 'SELECT "category", count(*) as "total" ' \
                'FROM "item" ' \
                'WHERE "department" = ? ' \
                'GROUP BY "category" ' \
                'HAVING "total" > 3'
        builder.get_connection().select.return_value = results
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results: results)
        result = builder.select('category', QueryExpression('count(*) as "total"'))\
            .from_('item')\
            .where('department', '=', 'popular')\
            .group_by('category')\
            .having('total', '>', QueryExpression('3'))\
            .get()

        builder.get_connection().select.assert_called_once_with(
            query,
            ['popular'],
            True
        )
        builder.get_processor().process_select.assert_called_once_with(
            builder,
            results
        )
        self.assertEqual(results, result)
        self.assertEqual(['popular'], builder.get_bindings())

    def test_raw_havings(self):
        builder = self.get_builder()
        builder.select('*').from_('users').having_raw('user_foo < user_bar')
        self.assertEqual(
            'SELECT * FROM "users" HAVING user_foo < user_bar',
            builder.to_sql()
        )
        self.assertEqual([], builder.get_bindings())

        builder = self.get_builder()
        builder.select('*').from_('users').having('foo', '=', 1).or_having_raw('user_foo < user_bar')
        self.assertEqual(
            'SELECT * FROM "users" HAVING "foo" = ? OR user_foo < user_bar',
            builder.to_sql()
        )
        self.assertEqual([1], builder.get_bindings())

    def test_limits_and_offsets(self):
        builder = self.get_builder()
        builder.select('*').from_('users').offset(5).limit(10)
        self.assertEqual('SELECT * FROM "users" LIMIT 10 OFFSET 5', builder.to_sql())

        builder = self.get_builder()
        builder.select('*').from_('users').skip(5).take(10)
        self.assertEqual('SELECT * FROM "users" LIMIT 10 OFFSET 5', builder.to_sql())

        builder = self.get_builder()
        builder.select('*').from_('users').skip(-5).take(10)
        self.assertEqual('SELECT * FROM "users" LIMIT 10 OFFSET 0', builder.to_sql())

        builder = self.get_builder()
        builder.select('*').from_('users').for_page(2, 15)
        self.assertEqual('SELECT * FROM "users" LIMIT 15 OFFSET 15', builder.to_sql())

        builder = self.get_builder()
        builder.select('*').from_('users').for_page(-2, 15)
        self.assertEqual('SELECT * FROM "users" LIMIT 15 OFFSET 0', builder.to_sql())

    def test_where_shortcut(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where('id', 1).or_where('name', 'foo')
        self.assertEqual(
            'SELECT * FROM "users" WHERE "id" = ? OR "name" = ?',
            builder.to_sql()
        )
        self.assertEqual([1, 'foo'], builder.get_bindings())

    def test_nested_wheres(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where('email', '=', 'foo').or_where(
            builder.new_query().where('name', '=', 'bar').where('age', '=', 25)
        )
        self.assertEqual(
            'SELECT * FROM "users" WHERE "email" = ? OR ("name" = ? AND "age" = ?)',
            builder.to_sql()
        )
        self.assertEqual(['foo', 'bar', 25], builder.get_bindings())

    def test_full_sub_selects(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where('email', '=', 'foo').or_where(
            'id', '=', builder.new_query().select(QueryExpression('max(id)')).from_('users').where('email', '=', 'bar')
        )
        self.assertEqual(
            'SELECT * FROM "users" WHERE "email" = ? OR "id" = (SELECT max(id) FROM "users" WHERE "email" = ?)',
            builder.to_sql()
        )
        self.assertEqual(['foo', 'bar'], builder.get_bindings())

    def test_where_exists(self):
        builder = self.get_builder()
        builder.select('*').from_('orders').where_exists(
            self.get_builder().select('*').from_('products').where('products.id', '=', QueryExpression('"orders"."id"'))
        )
        self.assertEqual(
            'SELECT * FROM "orders" '
            'WHERE EXISTS (SELECT * FROM "products" WHERE "products"."id" = "orders"."id")',
            builder.to_sql()
        )
        self.assertEqual([], builder.get_bindings())

        builder = self.get_builder()
        builder.select('*').from_('orders').where_not_exists(
            self.get_builder().select('*').from_('products').where('products.id', '=', QueryExpression('"orders"."id"'))
        )
        self.assertEqual(
            'SELECT * FROM "orders" '
            'WHERE NOT EXISTS (SELECT * FROM "products" WHERE "products"."id" = "orders"."id")',
            builder.to_sql()
        )
        self.assertEqual([], builder.get_bindings())

        builder = self.get_builder()
        builder.select('*').from_('orders').where('id', '=', 1).or_where_exists(
            self.get_builder().select('*').from_('products').where('products.id', '=', QueryExpression('"orders"."id"'))
        )
        self.assertEqual(
            'SELECT * FROM "orders" WHERE "id" = ? '
            'OR EXISTS (SELECT * FROM "products" WHERE "products"."id" = "orders"."id")',
            builder.to_sql()
        )
        self.assertEqual([1], builder.get_bindings())

        builder = self.get_builder()
        builder.select('*').from_('orders').where('id', '=', 1).or_where_not_exists(
            self.get_builder().select('*').from_('products').where('products.id', '=', QueryExpression('"orders"."id"'))
        )
        self.assertEqual(
            'SELECT * FROM "orders" WHERE "id" = ? '
            'OR NOT EXISTS (SELECT * FROM "products" WHERE "products"."id" = "orders"."id")',
            builder.to_sql()
        )
        self.assertEqual([1], builder.get_bindings())

    def test_basic_joins(self):
        builder = self.get_builder()
        builder.select('*').from_('users')\
            .join('contacts', 'users.id', '=', 'contacts.id')\
            .left_join('photos', 'users.id', '=', 'photos.user_id')
        self.assertEqual(
            'SELECT * FROM "users" '
            'INNER JOIN "contacts" ON "users"."id" = "contacts"."id" '
            'LEFT JOIN "photos" ON "users"."id" = "photos"."user_id"',
            builder.to_sql()
        )

        builder = self.get_builder()
        builder.select('*').from_('users')\
            .left_join_where('photos', 'users.id', '=', 3)\
            .join_where('photos', 'users.id', '=', 'foo')
        self.assertEqual(
            'SELECT * FROM "users" '
            'LEFT JOIN "photos" ON "users"."id" = ? '
            'INNER JOIN "photos" ON "users"."id" = ?',
            builder.to_sql()
        )
        self.assertEqual([3, 'foo'], builder.get_bindings())

    def test_complex_joins(self):
        builder = self.get_builder()
        builder.select('*').from_('users').join(
            JoinClause('contacts')
            .on('users.id', '=', 'contacts.id')
            .or_on('users.name', '=', 'contacts.name')
        )
        self.assertEqual(
            'SELECT * FROM "users" '
            'INNER JOIN "contacts" ON "users"."id" = "contacts"."id" '
            'OR "users"."name" = "contacts"."name"',
            builder.to_sql()
        )

        builder = self.get_builder()
        builder.select('*').from_('users').join(
            JoinClause('contacts')
            .where('users.id', '=', 'foo')
            .or_where('users.name', '=', 'bar')
        )
        self.assertEqual(
            'SELECT * FROM "users" '
            'INNER JOIN "contacts" ON "users"."id" = ? '
            'OR "users"."name" = ?',
            builder.to_sql()
        )
        self.assertEqual(['foo', 'bar'], builder.get_bindings())

        self.assertEqual(
            'SELECT * FROM "users" '
            'INNER JOIN "contacts" ON "users"."id" = ? '
            'OR "users"."name" = ?',
            builder.to_sql()
        )
        self.assertEqual(['foo', 'bar'], builder.get_bindings())

        builder = self.get_builder()
        builder.select('*').from_('users').left_join(
            JoinClause('contacts')
            .where('users.id', '=', 'foo')
            .or_where('users.name', '=', 'bar')
        )
        self.assertEqual(
            'SELECT * FROM "users" '
            'LEFT JOIN "contacts" ON "users"."id" = ? '
            'OR "users"."name" = ?',
            builder.to_sql()
        )
        self.assertEqual(['foo', 'bar'], builder.get_bindings())

        self.assertEqual(
            'SELECT * FROM "users" '
            'LEFT JOIN "contacts" ON "users"."id" = ? '
            'OR "users"."name" = ?',
            builder.to_sql()
        )
        self.assertEqual(['foo', 'bar'], builder.get_bindings())

    def test_join_where_null(self):
        builder = self.get_builder()
        builder.select('*').from_('users').join(
            JoinClause('contacts')
            .on('users.id', '=', 'contacts.id')
            .where_null('contacts.deleted_at')
        )
        self.assertEqual(
            'SELECT * FROM "users" '
            'INNER JOIN "contacts" '
            'ON "users"."id" = "contacts"."id" '
            'AND "contacts"."deleted_at" IS NULL',
            builder.to_sql()
        )

        builder = self.get_builder()
        builder.select('*').from_('users').join(
            JoinClause('contacts')
            .on('users.id', '=', 'contacts.id')
            .or_where_null('contacts.deleted_at')
        )
        self.assertEqual(
            'SELECT * FROM "users" '
            'INNER JOIN "contacts" '
            'ON "users"."id" = "contacts"."id" '
            'OR "contacts"."deleted_at" IS NULL',
            builder.to_sql()
        )

    def test_join_where_not_null(self):
        builder = self.get_builder()
        builder.select('*').from_('users').join(
            JoinClause('contacts')
            .on('users.id', '=', 'contacts.id')
            .where_not_null('contacts.deleted_at')
        )
        self.assertEqual(
            'SELECT * FROM "users" '
            'INNER JOIN "contacts" '
            'ON "users"."id" = "contacts"."id" '
            'AND "contacts"."deleted_at" IS NOT NULL',
            builder.to_sql()
        )

        builder = self.get_builder()
        builder.select('*').from_('users').join(
            JoinClause('contacts')
            .on('users.id', '=', 'contacts.id')
            .or_where_not_null('contacts.deleted_at')
        )
        self.assertEqual(
            'SELECT * FROM "users" '
            'INNER JOIN "contacts" '
            'ON "users"."id" = "contacts"."id" '
            'OR "contacts"."deleted_at" IS NOT NULL',
            builder.to_sql()
        )

    def test_raw_expression_in_select(self):
        builder = self.get_builder()
        builder.select(QueryExpression('substr(foo, 6)')).from_('users')
        self.assertEqual('SELECT substr(foo, 6) FROM "users"', builder.to_sql())

    def test_find_return_first_result_by_id(self):
        builder = self.get_builder()
        query = 'SELECT * FROM "users" WHERE "id" = ? LIMIT 1'
        results = [{
            'foo': 'bar'
        }]
        builder.get_connection().select.return_value = results
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results)
        result = builder.from_('users').find(1)
        builder.get_connection().select.assert_called_once_with(
            query, [1], True
        )
        builder.get_processor().process_select.assert_called_once_with(builder, results)
        self.assertEqual(result, results[0])

    def test_first_return_first_result(self):
        builder = self.get_builder()
        query = 'SELECT * FROM "users" WHERE "id" = ? LIMIT 1'
        results = [{
            'foo': 'bar'
        }]
        builder.get_connection().select.return_value = results
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results)
        result = builder.from_('users').where('id', '=', 1).first()
        builder.get_connection().select.assert_called_once_with(
            query, [1], True
        )
        builder.get_processor().process_select.assert_called_once_with(builder, results)
        self.assertEqual(result, results[0])

    def test_list_methods_gets_list_of_colmun_values(self):
        builder = self.get_builder()
        results = [
            {'foo': 'bar'}, {'foo': 'baz'}
        ]
        builder.get_connection().select.return_value = results
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results)
        result = builder.from_('users').where('id', '=', 1).lists('foo')
        self.assertEqual(['bar', 'baz'], result)

        builder = self.get_builder()
        results = [
            {'id': 1, 'foo': 'bar'}, {'id': 10, 'foo': 'baz'}
        ]
        builder.get_connection().select.return_value = results
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results)
        result = builder.from_('users').where('id', '=', 1).lists('foo', 'id')
        self.assertEqual({1: 'bar', 10: 'baz'}, result)

    def test_implode(self):
        builder = self.get_builder()
        results = [
            {'foo': 'bar'}, {'foo': 'baz'}
        ]
        builder.get_connection().select.return_value = results
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results)
        result = builder.from_('users').where('id', '=', 1).implode('foo')
        self.assertEqual('barbaz', result)

        builder = self.get_builder()
        results = [
            {'foo': 'bar'}, {'foo': 'baz'}
        ]
        builder.get_connection().select.return_value = results
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results)
        result = builder.from_('users').where('id', '=', 1).implode('foo', ',')
        self.assertEqual('bar,baz', result)

    def test_pluck_return_single_column(self):
        builder = self.get_builder()
        query = 'SELECT "foo" FROM "users" WHERE "id" = ? LIMIT 1'
        results = [{'foo': 'bar'}]
        builder.get_connection().select.return_value = results
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results)
        result = builder.from_('users').where('id', '=', 1).pluck('foo')
        builder.get_connection().select.assert_called_once_with(
            query, [1], True
        )
        builder.get_processor().process_select.assert_called_once_with(builder, results)
        self.assertEqual('bar', result)

    def test_aggegate_functions(self):
        builder = self.get_builder()
        query = 'SELECT COUNT(*) AS aggregate FROM "users"'
        results = [{'aggregate': 1}]
        builder.get_connection().select.return_value = results
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results)
        result = builder.from_('users').count()
        builder.get_connection().select.assert_called_once_with(
            query, [], True
        )
        builder.get_processor().process_select.assert_called_once_with(builder, results)
        self.assertEqual(1, result)

        builder = self.get_builder()
        query = 'SELECT COUNT(*) AS aggregate FROM "users" LIMIT 1'
        results = [{'aggregate': 1}]
        builder.get_connection().select.return_value = results
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results_)
        result = builder.from_('users').exists()
        builder.get_connection().select.assert_called_once_with(
            query, [], True
        )
        builder.get_processor().process_select.assert_called_once_with(builder, results)
        self.assertTrue(result)

        builder = self.get_builder()
        query = 'SELECT MAX("id") AS aggregate FROM "users"'
        results = [{'aggregate': 1}]
        builder.get_connection().select.return_value = results
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results_)
        result = builder.from_('users').max('id')
        builder.get_connection().select.assert_called_once_with(
            query, [], True
        )
        builder.get_processor().process_select.assert_called_once_with(builder, results)
        self.assertEqual(1, result)

        builder = self.get_builder()
        query = 'SELECT MIN("id") AS aggregate FROM "users"'
        results = [{'aggregate': 1}]
        builder.get_connection().select.return_value = results
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results_)
        result = builder.from_('users').min('id')
        builder.get_connection().select.assert_called_once_with(
            query, [], True
        )
        builder.get_processor().process_select.assert_called_once_with(builder, results)
        self.assertEqual(1, result)

        builder = self.get_builder()
        query = 'SELECT SUM("id") AS aggregate FROM "users"'
        results = [{'aggregate': 1}]
        builder.get_connection().select.return_value = results
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results_)
        result = builder.from_('users').sum('id')
        builder.get_connection().select.assert_called_once_with(
            query, [], True
        )
        builder.get_processor().process_select.assert_called_once_with(builder, results)
        self.assertEqual(1, result)

        builder = self.get_builder()
        query = 'SELECT AVG("id") AS aggregate FROM "users"'
        results = [{'aggregate': 1}]
        builder.get_connection().select.return_value = results
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results_)
        result = builder.from_('users').avg('id')
        builder.get_connection().select.assert_called_once_with(
            query, [], True
        )
        builder.get_processor().process_select.assert_called_once_with(builder, results)
        self.assertEqual(1, result)

    def test_aggregate_reset_followed_by_get(self):
        builder = self.get_builder()
        query = 'SELECT COUNT(*) AS aggregate FROM "users"'
        builder.get_connection().select.return_value = [{'aggregate': 1}]
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results_)
        builder.from_('users').select('column1', 'column2')
        count = builder.count()
        builder.get_connection().select.assert_called_once_with(
            query, [], True
        )
        builder.get_processor().process_select.assert_called_once_with(builder, [{'aggregate': 1}])
        self.assertEqual(1, count)

        builder.get_connection().select.reset_mock()
        builder.get_processor().process_select.reset_mock()
        query = 'SELECT SUM("id") AS aggregate FROM "users"'
        builder.get_connection().select.return_value = [{'aggregate': 2}]
        sum_ = builder.sum('id')
        builder.get_connection().select.assert_called_once_with(
            query, [], True
        )
        builder.get_processor().process_select.assert_called_once_with(builder, [{'aggregate': 2}])
        self.assertEqual(2, sum_)

        builder.get_connection().select.reset_mock()
        builder.get_processor().process_select.reset_mock()
        query = 'SELECT "column1", "column2" FROM "users"'
        builder.get_connection().select.return_value = [{'column1': 'foo', 'column2': 'bar'}]
        result = builder.get()
        builder.get_connection().select.assert_called_once_with(
            query, [], True
        )
        builder.get_processor().process_select.assert_called_once_with(builder, [{'column1': 'foo', 'column2': 'bar'}])
        self.assertEqual([{'column1': 'foo', 'column2': 'bar'}], result)

    def test_aggregate_reset_followed_by_select_get(self):
        builder = self.get_builder()
        query = 'SELECT COUNT("column1") AS aggregate FROM "users"'
        builder.get_connection().select.return_value = [{'aggregate': 1}]
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results_)
        builder.from_('users')
        count = builder.count('column1')
        builder.get_connection().select.assert_called_once_with(
            query, [], True
        )
        builder.get_processor().process_select.assert_called_once_with(builder, [{'aggregate': 1}])
        self.assertEqual(1, count)

        builder.get_connection().select.reset_mock()
        builder.get_processor().process_select.reset_mock()
        query = 'SELECT "column2", "column3" FROM "users"'
        builder.get_connection().select.return_value = [{'column2': 'foo', 'column3': 'bar'}]
        result = builder.select('column2', 'column3').get()
        builder.get_connection().select.assert_called_once_with(
            query, [], True
        )
        builder.get_processor().process_select.assert_called_once_with(builder, [{'column2': 'foo', 'column3': 'bar'}])
        self.assertEqual([{'column2': 'foo', 'column3': 'bar'}], result)

    def test_aggregate_reset_followed_by_get_with_columns(self):
        builder = self.get_builder()
        query = 'SELECT COUNT("column1") AS aggregate FROM "users"'
        builder.get_connection().select.return_value = [{'aggregate': 1}]
        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results_)
        builder.from_('users')
        count = builder.count('column1')
        builder.get_connection().select.assert_called_once_with(
            query, [], True
        )
        builder.get_processor().process_select.assert_called_once_with(builder, [{'aggregate': 1}])
        self.assertEqual(1, count)

        builder.get_connection().select.reset_mock()
        builder.get_processor().process_select.reset_mock()
        query = 'SELECT "column2", "column3" FROM "users"'
        builder.get_connection().select.return_value = [{'column2': 'foo', 'column3': 'bar'}]
        result = builder.get(['column2', 'column3'])
        builder.get_connection().select.assert_called_once_with(
            query, [], True
        )
        builder.get_processor().process_select.assert_called_once_with(builder, [{'column2': 'foo', 'column3': 'bar'}])
        self.assertEqual([{'column2': 'foo', 'column3': 'bar'}], result)

    def test_insert_method(self):
        builder = self.get_builder()
        query = 'INSERT INTO "users" ("email") VALUES (?)'
        builder.get_connection().insert.return_value = True
        result = builder.from_('users').insert({'email': 'foo'})
        builder.get_connection().insert.assert_called_once_with(
            query, ['foo']
        )
        self.assertTrue(result)

    def test_insert_method_with_keyword_arguments(self):
        builder = self.get_builder()
        query = 'INSERT INTO "users" ("email") VALUES (?)'
        builder.get_connection().insert.return_value = True
        result = builder.from_('users').insert({'email': 'foo'})
        builder.get_connection().insert.assert_called_once_with(
            query, ['foo']
        )
        self.assertTrue(result)

    def test_sqlite_multiple_insert(self):
        builder = self.get_sqlite_builder()
        query = 'INSERT INTO "users" ("email", "name") ' \
                'SELECT ? AS "email", ? AS "name" UNION ALL SELECT ? AS "email", ? AS "name"'
        builder.get_connection().insert.return_value = True
        result = builder.from_('users').insert([
            {'email': 'foo', 'name': 'john'},
            {'email': 'bar', 'name': 'jane'}
        ])
        builder.get_connection().insert.assert_called_once_with(
            query, ['foo', 'john', 'bar', 'jane']
        )
        self.assertTrue(result)

    def test_insert_get_id_method(self):
        builder = self.get_builder()
        builder.get_processor().process_insert_get_id.return_value = 1
        result = builder.from_('users').insert_get_id({
            'email': 'foo',
            'bar': QueryExpression('bar')
        })
        builder.get_processor().process_insert_get_id.assert_called_once_with(
            builder, 'INSERT INTO "users" ("bar", "email") VALUES (bar, ?)', ['foo'], None
        )
        self.assertEqual(1, result)

    def test_insert_get_id_with_sequence(self):
        builder = self.get_builder()
        builder.get_processor().process_insert_get_id.return_value = 1
        result = builder.from_('users').insert_get_id({
            'email': 'foo',
            'bar': QueryExpression('bar')
        }, 'id')
        builder.get_processor().process_insert_get_id.assert_called_once_with(
            builder, 'INSERT INTO "users" ("bar", "email") VALUES (bar, ?)', ['foo'], 'id'
        )
        self.assertEqual(1, result)

    def test_insert_get_id_respects_raw_bindings(self):
        builder = self.get_builder()
        builder.get_processor().process_insert_get_id.return_value = 1
        result = builder.from_('users').insert_get_id({
            'email': QueryExpression('CURRENT_TIMESTAMP'),
        })
        builder.get_processor().process_insert_get_id.assert_called_once_with(
            builder, 'INSERT INTO "users" ("email") VALUES (CURRENT_TIMESTAMP)', [], None
        )
        self.assertEqual(1, result)

    def test_update(self):
        builder = self.get_builder()
        query = 'UPDATE "users" SET "email" = ?, "name" = ? WHERE "id" = ?'
        builder.get_connection().update.return_value = 1
        result = builder.from_('users').where('id', '=', 1).update(email='foo', name='bar')
        builder.get_connection().update.assert_called_with(
            query, ['foo', 'bar', 1]
        )
        self.assertEqual(1, result)
        
        builder = self.get_mysql_builder()
        marker = builder.get_grammar().get_marker()
        query = 'UPDATE `users` SET `email` = %s, `name` = %s WHERE `id` = %s' % (marker, marker, marker)
        builder.get_connection().update.return_value = 1
        result = builder.from_('users').where('id', '=', 1).update(email='foo', name='bar')
        builder.get_connection().update.assert_called_with(
            query, ['foo', 'bar', 1]
        )
        self.assertEqual(1, result)

    def test_update_with_dictionaries(self):
        builder = self.get_builder()
        query = 'UPDATE "users" SET "email" = ?, "name" = ? WHERE "id" = ?'
        builder.get_connection().update.return_value = 1
        result = builder.from_('users').where('id', '=', 1).update({'email': 'foo', 'name': 'bar'})
        builder.get_connection().update.assert_called_with(
            query, ['foo', 'bar', 1]
        )
        self.assertEqual(1, result)
        builder = self.get_builder()

        query = 'UPDATE "users" SET "email" = ?, "name" = ? WHERE "id" = ?'
        builder.get_connection().update.return_value = 1
        result = builder.from_('users').where('id', '=', 1).update({'email': 'foo'}, name='bar')
        builder.get_connection().update.assert_called_with(
            query, ['foo', 'bar', 1]
        )
        self.assertEqual(1, result)

    def test_update_with_joins(self):
        builder = self.get_builder()
        query = 'UPDATE "users" ' \
                'INNER JOIN "orders" ON "users"."id" = "orders"."user_id" ' \
                'SET "email" = ?, "name" = ? WHERE "id" = ?'
        builder.get_connection().update.return_value = 1
        result = builder.from_('users')\
            .join('orders', 'users.id', '=', 'orders.user_id')\
            .where('id', '=', 1)\
            .update(email='foo', name='bar')
        builder.get_connection().update.assert_called_with(
            query, ['foo', 'bar', 1]
        )
        self.assertEqual(1, result)

    def test_update_on_postgres(self):
        builder = self.get_postgres_builder()
        marker = builder.get_grammar().get_marker()
        query = 'UPDATE "users" SET "email" = %s, "name" = %s WHERE "id" = %s' % (marker, marker, marker)
        builder.get_connection().update.return_value = 1
        result = builder.from_('users').where('id', '=', 1).update(email='foo', name='bar')
        builder.get_connection().update.assert_called_with(
            query, ['foo', 'bar', 1]
        )
        self.assertEqual(1, result)

    def test_update_with_joins_on_postgres(self):
        builder = self.get_postgres_builder()
        marker = builder.get_grammar().get_marker()
        query = 'UPDATE "users" ' \
                'SET "email" = %s, "name" = %s ' \
                'FROM "orders" WHERE "id" = %s AND "users"."id" = "orders"."user_id"'\
                % (marker, marker, marker)
        builder.get_connection().update.return_value = 1
        result = builder.from_('users')\
            .join('orders', 'users.id', '=', 'orders.user_id')\
            .where('id', '=', 1)\
            .update(email='foo', name='bar')
        builder.get_connection().update.assert_called_once_with(
            query, ['foo', 'bar', 1]
        )
        self.assertEqual(1, result)

    def test_update_respects_raw(self):
        builder = self.get_builder()
        marker = '?'
        query = 'UPDATE "users" SET "email" = foo, "name" = %s WHERE "id" = %s' % (marker, marker)
        builder.get_connection().update.return_value = 1
        result = builder.from_('users').where('id', '=', 1).update(email=QueryExpression('foo'), name='bar')
        builder.get_connection().update.assert_called_once_with(
            query, ['bar', 1]
        )
        self.assertEqual(1, result)

    def test_delete(self):
        builder = self.get_builder()
        query = 'DELETE FROM "users" WHERE "email" = ?'
        builder.get_connection().delete.return_value = 1
        result = builder.from_('users').where('email', '=', 'foo').delete()
        builder.get_connection().delete.assert_called_once_with(
            query, ['foo']
        )
        self.assertEqual(1, result)

        builder = self.get_builder()
        query = 'DELETE FROM "users" WHERE "id" = ?'
        builder.get_connection().delete.return_value = 1
        result = builder.from_('users').delete(1)
        builder.get_connection().delete.assert_called_once_with(
            query, [1]
        )
        self.assertEqual(1, result)

    def test_delete_with_join(self):
        builder = self.get_mysql_builder()
        marker = builder.get_grammar().get_marker()
        query = 'DELETE `users` FROM `users` ' \
                'INNER JOIN `contacts` ON `users`.`id` = `contacts`.`id` WHERE `email` = %s' % marker
        builder.get_connection().delete.return_value = 1
        result = builder.from_('users')\
            .join('contacts', 'users.id', '=', 'contacts.id')\
            .where('email', '=', 'foo')\
            .delete()
        builder.get_connection().delete.assert_called_once_with(
            query, ['foo']
        )
        self.assertEqual(1, result)

        builder = self.get_mysql_builder()
        marker = builder.get_grammar().get_marker()
        query = 'DELETE `users` FROM `users` ' \
                'INNER JOIN `contacts` ON `users`.`id` = `contacts`.`id` WHERE `id` = %s' % marker
        builder.get_connection().delete.return_value = 1
        result = builder.from_('users')\
            .join('contacts', 'users.id', '=', 'contacts.id')\
            .delete(1)
        builder.get_connection().delete.assert_called_once_with(
            query, [1]
        )
        self.assertEqual(1, result)

    def test_truncate(self):
        builder = self.get_builder()
        query = 'TRUNCATE "users"'
        builder.from_('users').truncate()
        builder.get_connection().statement.assert_called_once_with(
            query, []
        )

        builder = self.get_sqlite_builder()
        builder.from_('users')
        self.assertEqual({
            'DELETE FROM sqlite_sequence WHERE name = ?': ['users'],
            'DELETE FROM "users"': []
        }, builder.get_grammar().compile_truncate(builder))

    def test_postgres_insert_get_id(self):
        builder = self.get_postgres_builder()
        marker = builder.get_grammar().get_marker()
        query = 'INSERT INTO "users" ("email") VALUES (%s) RETURNING "id"' % marker
        builder.get_processor().process_insert_get_id.return_value = 1
        result = builder.from_('users').insert_get_id({'email': 'foo'}, 'id')
        builder.get_processor().process_insert_get_id.assert_called_once_with(
            builder, query, ['foo'], 'id'
        )
        self.assertEqual(1, result)

    def test_mysql_wrapping(self):
        builder = self.get_mysql_builder()
        builder.select('*').from_('users')
        self.assertEqual(
            'SELECT * FROM `users`',
            builder.to_sql()
        )

    def test_merge_wheres_can_merge_wheres_and_bindings(self):
        builder = self.get_builder()
        builder.wheres = ['foo']
        builder.merge_wheres(['wheres'], ['foo', 'bar'])
        self.assertEqual(['foo', 'wheres'], builder.wheres)
        self.assertEqual(['foo', 'bar'], builder.get_bindings())

    def test_where_with_null_second_parameter(self):
        builder = self.get_builder()
        builder.select('*').from_('users').where('foo', None)
        self.assertEqual(
            'SELECT * FROM "users" WHERE "foo" IS NULL',
            builder.to_sql()
        )

    def test_dynamic_where(self):
        method = 'where_foo_bar_and_baz_or_boom'
        parameters = ['john', 'jane', 'bam']

        builder = self.get_builder()
        builder.where = mock.MagicMock(return_value=builder)

        getattr(builder, method)(*parameters)

        builder.where.assert_has_calls([
            mock.call('foo_bar', '=', parameters[0], 'and'),
            mock.call('baz', '=', parameters[1], 'and'),
            mock.call('boom', '=', parameters[2], 'or')
        ])

    def test_dynamic_where_is_not_greedy(self):
        method = 'where_ios_version_and_android_version_or_orientation'
        parameters = ['6.1', '4.2', 'Vertical']

        builder = self.get_builder()
        builder.where = mock.MagicMock(return_value=builder)

        getattr(builder, method)(*parameters)

        builder.where.assert_has_calls([
            mock.call('ios_version', '=', parameters[0], 'and'),
            mock.call('android_version', '=', parameters[1], 'and'),
            mock.call('orientation', '=', parameters[2], 'or')
        ])

    def test_call_triggers_dynamic_where(self):
        builder = self.get_builder()

        self.assertEqual(builder, builder.where_foo_and_bar('baz', 'boom'))
        self.assertEqual(2, len(builder.wheres))

    def test_builder_raises_exception_with_undefined_method(self):
        builder = self.get_builder()

        try:
            builder.do_not_exist()
            self.fail('Builder did not raise and AttributeError exception')
        except AttributeError:
            self.assertTrue(True)

    def test_mysql_lock(self):
        builder = self.get_mysql_builder()
        marker = builder.get_grammar().get_marker()
        builder.select('*').from_('foo').where('bar', '=', 'baz').lock()
        self.assertEqual(
            'SELECT * FROM `foo` WHERE `bar` = %s FOR UPDATE' % marker,
            builder.to_sql()
        )
        self.assertEqual(['baz'], builder.get_bindings())

        builder = self.get_mysql_builder()
        marker = builder.get_grammar().get_marker()
        builder.select('*').from_('foo').where('bar', '=', 'baz').lock(False)
        self.assertEqual(
            'SELECT * FROM `foo` WHERE `bar` = %s LOCK IN SHARE MODE' % marker,
            builder.to_sql()
        )
        self.assertEqual(['baz'], builder.get_bindings())

    def test_postgres_lock(self):
        builder = self.get_postgres_builder()
        marker = builder.get_grammar().get_marker()
        builder.select('*').from_('foo').where('bar', '=', 'baz').lock()
        self.assertEqual(
            'SELECT * FROM "foo" WHERE "bar" = %s FOR UPDATE' % marker,
            builder.to_sql()
        )
        self.assertEqual(['baz'], builder.get_bindings())

        builder = self.get_postgres_builder()
        marker = builder.get_grammar().get_marker()
        builder.select('*').from_('foo').where('bar', '=', 'baz').lock(False)
        self.assertEqual(
            'SELECT * FROM "foo" WHERE "bar" = %s FOR SHARE' % marker,
            builder.to_sql()
        )
        self.assertEqual(['baz'], builder.get_bindings())

    def test_binding_order(self):
        expected_sql = 'SELECT * FROM "users" ' \
                       'INNER JOIN "othertable" ON "bar" = ? ' \
                       'WHERE "registered" = ? ' \
                       'GROUP BY "city" ' \
                       'HAVING "population" > ? ' \
                       'ORDER BY match ("foo") against(?)'
        expected_bindings = ['foo', True, 3, 'bar']

        builder = self.get_builder()
        builder.select('*').from_('users')\
            .order_by_raw('match ("foo") against(?)', ['bar'])\
            .where('registered', True)\
            .group_by('city')\
            .having('population', '>', 3)\
            .join(JoinClause('othertable').where('bar', '=', 'foo'))

        self.assertEqual(expected_sql, builder.to_sql())
        self.assertEqual(expected_bindings, builder.get_bindings())

    def test_add_binding_with_list_merges_bindings(self):
        builder = self.get_builder()
        builder.add_binding(['foo', 'bar'])
        builder.add_binding(['baz'])
        self.assertEqual(['foo', 'bar', 'baz'], builder.get_bindings())

    def test_add_binding_with_list_merges_bindings_in_correct_order(self):
        builder = self.get_builder()
        builder.add_binding(['bar', 'baz'], 'having')
        builder.add_binding(['foo'], 'where')
        self.assertEqual(['foo', 'bar', 'baz'], builder.get_bindings())

    def test_merge_builders(self):
        builder = self.get_builder()
        builder.add_binding('foo', 'where')
        builder.add_binding('baz', 'having')
        other_builder = self.get_builder()
        other_builder.add_binding('bar', 'where')
        builder.merge_bindings(other_builder)
        self.assertEqual(['foo', 'bar', 'baz'], builder.get_bindings())

    def test_sub_select(self):
        builder = self.get_builder()
        marker = builder.get_grammar().get_marker()
        expected_sql = 'SELECT "foo", "bar", (SELECT "baz" FROM "two" WHERE "subkey" = %s) AS "sub" ' \
                       'FROM "one" WHERE "key" = %s' % (marker, marker)
        expected_bindings = ['subval', 'val']

        builder.from_('one').select('foo', 'bar').where('key', '=', 'val')
        builder.select_sub(builder.new_query().from_('two').select('baz').where('subkey', '=', 'subval'), 'sub')
        self.assertEqual(expected_sql, builder.to_sql())
        self.assertEqual(expected_bindings, builder.get_bindings())

    def test_chunk(self):
        builder = self.get_builder()
        results = [
            {'foo': 'bar'},
            {'foo': 'baz'},
            {'foo': 'bam'},
            {'foo': 'boom'}
        ]

        def select(query, bindings, _):
            index = int(re.search('OFFSET (\d+)', query).group(1))
            limit = int(re.search('LIMIT (\d+)', query).group(1))

            if index >= len(results):
                return []

            return results[index:index + limit]

        builder.get_connection().select.side_effect = select

        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results_)

        i = 0
        for users in builder.from_('users').chunk(1):
            self.assertEqual(users[0], results[i])

            i += 1

        builder = self.get_builder()
        results = [
            {'foo': 'bar'},
            {'foo': 'baz'},
            {'foo': 'bam'},
            {'foo': 'boom'}
        ]

        builder.get_connection().select.side_effect = select

        builder.get_processor().process_select = mock.MagicMock(side_effect=lambda builder_, results_: results_)

        for users in builder.from_('users').chunk(2):
            self.assertEqual(2, len(users))

    def get_mysql_builder(self):
        grammar = MySqlQueryGrammar()
        processor = MockProcessor().prepare_mock()
        connection = MockConnection().prepare_mock()

        return QueryBuilder(connection, grammar, processor)

    def get_sqlite_builder(self):
        grammar = SQLiteQueryGrammar()
        processor = MockProcessor().prepare_mock()
        connection = MockConnection().prepare_mock()

        return QueryBuilder(connection, grammar, processor)

    def get_postgres_builder(self):
        grammar = PostgresQueryGrammar()
        processor = MockProcessor().prepare_mock()
        connection = MockConnection().prepare_mock()

        return QueryBuilder(connection, grammar, processor)

    def get_builder(self):
        grammar = QueryGrammar()
        processor = MockProcessor().prepare_mock()
        connection = MockConnection().prepare_mock()

        return QueryBuilder(connection, grammar, processor)

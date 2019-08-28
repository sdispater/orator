# -*- coding: utf-8 -*-

from .sqlserver2012_keywords import SQLServer2012Keywords


class SQLServer2017Keywords(SQLServer2012Keywords):

    #  List acording to:
    #     https://docs.microsoft.com/en-us/sql/t-sql/language-elements/reserved-keywords-transact-sql?view=sql-server-2017
    KEYWORDS = [
        #  Azure SQL Data Warehouse exclusive reserver keywords
        'LABEL'
    ]

    def get_name(self):
        return 'SQLServer2017'

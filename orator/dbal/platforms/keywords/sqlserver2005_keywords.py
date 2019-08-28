# -*- coding: utf-8 -*-

from .sqlserver_keywords import SQLServerKeywords


class SQLServer2005Keywords(SQLServerKeywords):

    #  List acording to:
    #     http://msdn.microsoft.com/en-US/library/ms189822%28v=sql.90%29.aspx
    KEYWORDS = [
        'EXTERNAL',
        'PIVOT',
        'REVERT',
        'SECURITYAUDIT',
        'TABLESAMPLE',
        'UNPIVOT'
    ]

    def get_name(self):
        return 'SQLServer2005'

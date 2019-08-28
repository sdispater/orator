# -*- coding: utf-8 -*-

from .sqlserver2005_keywords import SQLServer2005Keywords


class SQLServer2008Keywords(SQLServer2005Keywords):

    #  List acording to:
    #     http://msdn.microsoft.com/en-us/library/ms189822%28v=sql.100%29.aspx
    KEYWORDS = [
        'MERGE'
    ]

    def get_name(self):
        return 'SQLServer2008'

# -*- coding: utf-8 -*-

from .sqlserver2008_keywords import SQLServer2008Keywords


class SQLServer2012Keywords(SQLServer2008Keywords):

    #  List acording to:
    #     http://msdn.microsoft.com/en-us/library/ms189822.aspx
    KEYWORDS = [
        'SEMANTICKEYPHRASETABLE',
        'SEMANTICSIMILARITYDETAILSTABLE',
        'SEMANTICSIMILARITYTABLE',
        'TRY_CONVERT',
        'WITHIN GROUP'
    ]

    def get_name(self):
        return 'SQLServer2012'

# -*- coding: utf-8 -*-

from .sqlserver_keywords import SQLServerKeywords


class MsSQLKeywords(SQLServerKeywords):

    def get_name(self):
        return 'MsSQL'

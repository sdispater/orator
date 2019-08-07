# -*- coding: utf-8 -*-

try:
    import pyodbc
except ImportError:
    pyodbc = None
    connection_class = object
    cursor_class = object
    row_class = object


from ..dbal.platforms import MySQLPlatform, MySQL57Platform
from .connector import Connector
from ..utils.qmarker import qmark, denullify
    
conn = pyodbc.connect('Driver={SQL Server};'
                      'Server=server_name;'
                      'Database=db_name;'
                      'Trusted_Connection=yes;')

cursor = conn.cursor()
# -*- coding: utf-8 -*-


class ConnectionResolverInterface(object):

    def connection(self, name=None):
        raise NotImplementedError()

    def get_default_connection(self):
        raise NotImplementedError()

    def set_default_connection(self, name):
        raise NotImplementedError()

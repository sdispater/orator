# -*- coding: utf-8 -*-


class Connector(object):

    def get_api(self):
        raise NotImplementedError()

    def connect(self, config):
        return self.get_api().connect(
            host=config['host'],
            database=config['database'],
            user=config['username'],
            password=config['password'],
        )

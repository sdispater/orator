# -*- coding: utf-8 -*-


class Connector(object):

    RESERVED_KEYWORDS = [
        'log_queries', 'driver', 'prefix', 'name'
    ]

    def get_api(self):
        raise NotImplementedError()

    def get_config(self, config):
        return {x: config[x] for x in config if x not in self.RESERVED_KEYWORDS}

    def connect(self, config):
        return self.get_api().connect(**self.get_config(config))

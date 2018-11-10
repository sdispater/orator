# -*- coding: utf-8 -*-


class TransactionError(ConnectionError):
    def __init__(self, previous, message=None):
        self.previous = previous
        self.message = "Transaction Error: "

# -*- coding: utf-8 -*-

import os
import errno


def value(val):
    if callable(val):
        return val()

    return val


def mkdir_p(path, mode=0o777):
    try:
        os.makedirs(path, mode)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

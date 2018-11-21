# -*- coding: utf-8 -*-

import os
import errno
import datetime


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


def serialize(value):
    if isinstance(value, datetime.datetime):
        if hasattr(value, "to_json"):
            value = value.to_json()
        else:
            value = value.isoformat()
    elif isinstance(value, list):
        value = list(map(serialize, value))
    elif isinstance(value, dict):
        for k, v in value.items():
            value[k] = serialize(v)

    return value

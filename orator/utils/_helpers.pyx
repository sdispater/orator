def value(val):
    if callable(val):
        return val()

    return val


def data_get(target, key, default=None):
    """
    Get an item from a list, a dict or an object using "dot" notation.

    :param target: The target element
    :type target: list or dict or object

    :param key: The key to get
    :type key: string or list

    :param default: The default value
    :type default: mixed

    :rtype: mixed
    """
    return _data_get(target, key, default)


cdef _data_get(target, key, default=None):
    from ..support import Collection

    if key is None:
        return target

    if not isinstance(key, list):
        key = key.split('.')

    for segment in key:
        if isinstance(target, (list, tuple)):
            try:
                target = target[segment]
            except IndexError:
                return value(default)
        elif isinstance(target, dict):
            try:
                target = target[segment]
            except IndexError:
                return value(default)
        elif isinstance(target, Collection):
            try:
                target = target[segment]
            except IndexError:
                return value(default)
        else:
            try:
                target = getattr(target, segment)
            except AttributeError:
                return value(default)

    return target

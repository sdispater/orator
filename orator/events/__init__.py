# -*- coding: utf-8 -*-

from blinker import Namespace


class Event(object):

    events = Namespace()

    @classmethod
    def fire(cls, name, *args, **kwargs):
        name = 'orator.%s' % name
        signal = cls.events.signal(name)

        for response in signal.send(*args, **kwargs):
            if response[1] is False:
                return False

    @classmethod
    def listen(cls, name, callback, *args, **kwargs):
        name = 'orator.%s' % name
        signal = cls.events.signal(name)

        signal.connect(callback, weak=False, *args, **kwargs)

    @classmethod
    def forget(cls, name, *args, **kwargs):
        name = 'orator.%s' % name
        signal = cls.events.signal(name)

        for receiver in signal.receivers:
            signal.disconnect(receiver, *args, **kwargs)


def event(name, *args, **kwargs):
    return Event.fire(name, *args, **kwargs)


def listen(name, callback, *args, **kwargs):
    return Event.listen(name, callback, *args, **kwargs)

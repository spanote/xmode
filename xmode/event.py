from collections import defaultdict
from typing import Callable


class EventDrivenObject(object):
    def __init__(self):
        self._events = defaultdict(set)

    def on(self, event_name:str, callback:Callable):
        self._events[event_name].add(callback)

    def trigger(self, event_name:str, *args, **kwargs):
        callbacks = self._events.get(event_name)

        if not callbacks:
            return

        [
            callback(*args, **kwargs)
            for callback in callbacks
        ]
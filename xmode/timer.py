from contextlib import contextmanager
from logging import getLogger
from time import time

_logger = getLogger(__name__)

@contextmanager
def measure_runtime(label):
    t = Timer()
    yield t
    t.show(label)


class Timer:
    def __init__(self):
        self._t0 = time()

    def show(self, label):
        global _logger
        _logger.info(f'{label} ({time() - self._t0:.3f}s)')

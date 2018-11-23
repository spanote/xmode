import logging
import time
import uuid

__log = logging.getLogger(__name__)
__known_recorders = {}

def get(name):
    global __known_recorders

    known_recorder = __known_recorders.get(name)

    if known_recorder is None:
        __known_recorders[name] = Recorder()

    return __known_recorders[name]


class Recorder:
    __instance__ = None

    def __init__(self):
        self.__id = str(uuid.uuid4())
        self.__starting_time = None
        self.__last_update = None
        self.__next_index = 0
        self.__raw_records = []
        self.__stopped = False

    def stop(self):
        self.record('profiler.stopped')
        self.__stopped = True

    def reset(self):
        self.__starting_time = None
        self.__last_update = None
        self.__next_index = 0
        self.__raw_records = []
        self.__stopped = False

    def record(self, event_name: str):
        if self.__stopped:
            return

        if not self.__starting_time:
            self.__starting_time = time.time()
            self.record('profiler.started')

        occurred_time = time.time()
        elapsed_time = occurred_time - self.__last_update if self.__last_update else 0

        __log.info(f'Profiler: {self.__id}: {event_name}: BE={elapsed_time:.3f}s (TE={time.time() - self.__starting_time:.3f}s)')

        self.__raw_records.append((self.__next_index, event_name, elapsed_time))

        self.__last_update = occurred_time
        self.__next_index += 1

    def export(self):
        event_sequence = []

        for index, event_name, elapsed_time in self.__raw_records:
            event_sequence.append(dict(i=index, e=event_name, t=elapsed_time))

        return dict(et=self.__raw_records[-1][0] - self.__starting_time, st=self.__starting_time, s=event_sequence)

    @classmethod
    def instance(cls):
        if cls.__instance__:
            return cls.__instance__

        cls.__instance__ = cls()

        return cls.__instance__

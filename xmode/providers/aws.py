from dataclasses import dataclass
from datetime import datetime
import logging
from pprint import pformat
from re import compile
from time import sleep, time
from typing import Optional

import boto3
from gallium.interface import ICommand
from xmode.event import EventDrivenObject
from xmode.utils.log_factory import make_basic_logger

module_logger = make_basic_logger(__name__, logging.DEBUG)
re_lambda_message = compile(r'^\[(?P<level>[A-Z]+)\]\t(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z)\t(?P<request_id>[A-Za-z\d\-]+)\t(?P<message>.*)$')


def to_stdout(obj):
    """
    Just to print the object for debugging.
    """
    module_logger.debug(pformat(obj, indent=2, width=160))


def event_to_stdout(event):
    ts = datetime.utcfromtimestamp(event.timestamp / 1000).strftime('%Y.%m.%d %H:%M:%S')
    message = event.message.strip()
    matches = re_lambda_message.search(message)

    if not matches:
        module_logger.info(f"{ts}: [?] {message}")
    else:
        context = matches.groupdict()
        module_logger.info(f"{ts}: [LAMBDA] {context.get('level')}: {context.get('request_id')}: {context.get('message')}")


class SessionFactory(object):
    @staticmethod
    def new(region_name:Optional[str], profile_name:Optional[str]):
        if profile_name:
            assert region_name, 'The region is required.'
            return boto3.Session(profile_name=profile_name, region_name=region_name)

        return boto3


class CloudWatchLogs(EventDrivenObject):
    backoff_period = 1  # one second back-off

    def __init__(self, session, log_group_name:str):
        super().__init__()

        self.session = session
        self.client = self.session.client('logs')
        self.log_group_name = log_group_name
        self._streams = None

    def tail(self, max_streams:int=5, follow:bool=False, initial_offset:int=900):
        offset = initial_offset
        trigger_event = self.trigger
        events = []

        try:
            while True:
                self._get_latest_log_streams(max_streams)

                for stream in self._streams:
                    for event in self._iterate_event_batch(stream['logStreamName'], offset=offset):
                        if event in events:
                            continue

                        events.append(event)

                events.sort(key=lambda x: x.timestamp)

                for event in events:
                    if event.notified:
                        continue

                    trigger_event('event', event)
                    event.notified = True

                if not follow:
                    break

                sleep(self.backoff_period) # Pause for a bit

                offset = max_streams + self.backoff_period
        except KeyboardInterrupt:
                pass

        self.trigger('done')

    def _iterate_event_batch(self, stream_name:str, offset:int, next_token:str=None):
        params = dict(logGroupName=self.log_group_name, logStreamName=stream_name, startTime=int(time() - offset))

        if next_token:
            params['nextToken'] = next_token

        logs_batch = self.client.get_log_events(**params)

        events = logs_batch['events']

        if 'nextToken' in logs_batch:
            events.extend(self._iterate_event_batch(stream_name, offset, logs_batch['nextToken']))
            # Recursively iterate until there is no more event to go on.

        return [Event(stream=stream_name, notified=False, **event) for event in events]


    def _get_latest_log_streams(self, limit:int):
        self._streams = []
        self._iterate_log_stream_batches(limit)
        self._streams.sort(key=lambda x: x['creationTime'])
        self.trigger('all_streams.ready', self._streams)

    def _iterate_log_stream_batches(self, limit, next_token:str=None):
        params = dict(logGroupName=self.log_group_name,
                      orderBy='LastEventTime',
                      limit=limit,
                      descending=True)

        if next_token:
            params['nextToken'] = next_token

        stream_batch = self.client.describe_log_streams(**params)

        self._streams.extend(stream_batch['logStreams'])

        if len(self._streams) < limit and 'nextToken' in stream_batch:
            self._iterate_log_stream_batches(stream_batch['nextToken'])
            # Recursively iterate until there is no more stream to go on.


@dataclass(frozen=False, eq=False)
class Event(object):
    timestamp:int
    message:str
    stream:str
    ingestionTime:int
    notified:bool

    def __eq__(self, other):
        return (
            self.timestamp == other.timestamp
            and self.message == other.message
            and self.stream == other.stream
            and self.ingestionTime == other.ingestionTime
        )

    def __hash__(self):
        return hash((self.timestamp, self.message, self.stream, self.ingestionTime))
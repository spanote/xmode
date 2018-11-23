from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import logging
from pprint import pformat
from re import compile
from time import time
from typing import Callable, Optional

import boto3
from gallium.interface import ICommand
from xmode.utils.log_factory import make_basic_logger

module_logger = make_basic_logger(__name__, logging.DEBUG)
re_lambda_message = compile('^\[(?P<level>[A-Z]+)\]\t(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z)\t(?P<request_id>[A-Za-z\d\-]+)\t(?P<message>.*)$')
# re_lambda_message = compile('^\[(?P<level>[A-Z]+)\]\s+(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z)\s+(?P<request_id>[A-Za-z\d\-]+)')


def to_stdout(obj):
    """
    Just to print the object for debugging.
    """
    module_logger.debug(pformat(obj, indent=2, width=160))


def event_to_stdout(data):
    ts = datetime.utcfromtimestamp(data['timestamp'] / 1000).strftime('%H:%M:%S')
    message = data['message'].strip()
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


class CloudWatchLogs(object):
    def __init__(self, session, log_group_name:str):
        self.session = session
        self.client = self.session.client('logs')
        self.log_group_name = log_group_name
        self._events = defaultdict(set)
        self._streams = None
        self._start_time = time() - 900

    def tail(self, max_streams:int=5, follow:bool=True):
        self._get_latest_log_streams(max_streams)
        [
            self._iterate_event_batch(stream['logStreamName'])
            for stream in self._streams
        ]
        self.trigger('done')

    def _iterate_event_batch(self, stream_name:str, next_token:str=None):
        params = dict(logGroupName=self.log_group_name, logStreamName=stream_name, startTime=int(self._start_time))
        trigger_event = self.trigger

        if next_token:
            params['nextToken'] = next_token

        logs_batch = self.client.get_log_events(**params)

        [
            trigger_event('event', event)
            for event in logs_batch['events']
        ]

        if 'nextToken' in logs_batch:
            self._iterate_event_batch(logs_batch['nextToken'])
            # Recursively iterate until there is no more event to go on.


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


# @dataclass
# class CloudWatchLog(object):
#     'logStreamName': '2018/11/05/[$LATEST]a64d6d2861a24c37b53f0a5e455eabc0',
#     'creationTime': 1541439056903,
#     'firstEventTimestamp': 1541439058210,
#     'lastEventTimestamp': 1541444635624,
#     'lastIngestionTime': 1541444635631,
#     'uploadSequenceToken': '49586181105883101785013855748757130475555404884098535122',
#     'arn':
#     'arn:aws:logs:us-east-1:861229788715:log-group:/aws/lambda/azul-service-dnastack:log-stream:2018/11/05/[$LATEST]a64d6d2861a24c37b53f0a5e455eabc0',
#     'storedBytes': 0


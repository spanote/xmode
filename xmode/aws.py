"""
Log Tracer
"""
from argparse import ArgumentParser, Namespace
from importlib import import_module

from gallium.interface import ICommand

from xmode.providers.aws import SessionFactory, CloudWatchLogs, event_to_stdout


class TailCloudWatchLog(ICommand):
    """
    Trace live CloudWatch logs
    """
    def identifier(self):
        return 'aws:logs:tail'

    def define(self, parser:ArgumentParser):
        parser.add_argument('--verbose', '-v',
                            action='store_true',
                            required=False,
                            help='Show log as it tails')
        parser.add_argument('--follow', '-f',
                            action='store_true',
                            required=False,
                            help='Constantly follow the updates')
        parser.add_argument('--aws-profile', '-p',
                            required=False,
                            help='User profile (used with assumed roles)')
        parser.add_argument('--aws-region', '-r',
                            required=False,
                            default='us-east-1',
                            help='User profile (used with assumed roles)')
        parser.add_argument('--max-streams', '-s',
                            required=False,
                            type=int,
                            default=2,
                            help='User profile (used with assumed roles)')
        parser.add_argument('log_group')
        parser.add_argument('event',
                            nargs='*',
                            help='Event and Fully qualified path to callable handler (e.g., event:samples.logs.aggregate)')

    def execute(self, args:Namespace):
        session = SessionFactory.new(args.aws_region, args.aws_profile)
        cwl = CloudWatchLogs(session, args.log_group)

        if args.event:
            for event_to_handler_path in args.event:
                event, handler_path = event_to_handler_path.split(':')
                blocks = handler_path.split('.')

                cwl.on(event,
                       getattr(import_module('.'.join(blocks[:-1])), blocks[-1]))

        if args.verbose:
            print('No event handlers provided. All events go to STDOUT.')
            cwl.on('event', event_to_stdout)

        cwl.tail(max_streams=args.max_streams, follow=args.follow)


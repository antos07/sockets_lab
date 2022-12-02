import argparse
import sys
from contextlib import suppress
from pathlib import Path
from typing import Optional

from loguru import logger

from .commandclient import CommandClient
from .commandserver import CommandServer


def main():
    """Entrypoint for the program"""

    parser = _build_parser()
    args = parser.parse_args()

    _setup_logs(args.verbose, args.log_to_file)

    if args.type == 'server':
        _run_server()
    else:
        _run_client(args.primes_file)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.prog = 'lab'
    parser.description = "Lab 'Sockets', variant 28 by Anton Trotsenko from K-27"
    parser.add_argument('--verbose', action='store_true', help='enable more detailed logs '
                                                               '(useful for debugging)')
    parser.add_argument('--log-to-file', type=Path, help='redirect logs to file LOG_FILE', metavar='LOG_FILE')

    subparsers = parser.add_subparsers(help='type of the program to run', dest='type', required=True)

    server_parser = subparsers.add_parser('server', help='run as a server')

    client_parser = subparsers.add_parser('client', help='run as a client')
    client_parser.add_argument('--primes-file', default='primes.txt', type=Path,
                               help='output file for primes (defaults to primes.txt)')

    return parser


def _setup_logs(verbose: bool, log_file: Optional[Path] = None):
    logger.remove()
    log_level = 'DEBUG' if verbose else 'INFO'
    log_file = str(log_file) if log_file else sys.stderr
    logger.add(log_file, level=log_level)


def _run_server():
    logger.info('Starting the server')
    with CommandServer() as server:
        with suppress(KeyboardInterrupt):
            server.run()
    logger.info('The server stopped')


def _run_client(primes_file: Path):
    logger.info('Starting the client')
    with CommandClient(primes_file) as client:
        with suppress(KeyboardInterrupt):
            client.run()
    logger.info('The client closed')


if __name__ == '__main__':
    main()

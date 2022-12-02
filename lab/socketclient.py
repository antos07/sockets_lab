import socket

from loguru import logger

from . import constants


class SocketClient:
    """A simple blocking socket-client.

    Uses `socket.socket` as the low-level backend. Socket's family is `AF_INET`,
    its type is `SOCK_STREAM` (so it uses TCP), and its protocol is default. Connects
    to the socket with the given address (localhost by default) and the given
    port (`lab.constants.DEFAULT_PORT` is used by default).

    Support the context manager protocol. Exiting the context manager is
    equivalent to `disconnect()`."""

    def __init__(self, address: str = constants.DEFAULT_HOST, port: int = constants.DEFAULT_PORT) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        addr = (address, port)
        logger.debug(f'Connecting to ({addr})')
        self._socket.connect(addr)
        logger.debug(f'Connected to ({addr})')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._socket.close()

    def run(self):
        """Runs client activity"""
        pass

    def disconnect(self):
        """Disconnects from the server."""
        logger.debug('Disconnecting')
        self._socket.close()
        logger.debug('Disconnected')

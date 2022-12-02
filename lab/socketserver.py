import socket

from loguru import logger

from . import constants

__all__ = ['SocketServer']

from .exceptions import ConnectionBrokenError


class SocketServer:
    """A simple blocking socket-server.

    Uses `socket.socket` as the low-level backend. Socket's family is `AF_INET`,
    its type is `SOCK_STREAM` (so it uses TCP), and its protocol is default.
    Binds socket to the given address (localhost by default) and
    the given port (`lab.constants.DEFAULT_PORT` is used by default).

    Support the context manager protocol. Exiting the context manager is
    equivalent to `shutdown()`.
    """

    MAX_CONNECTIONS = 1
    """Number of parallel connections allowed. This server supports 
    only 1 connection at a time."""

    def __init__(self, address: str = constants.DEFAULT_HOST, port: int = constants.DEFAULT_PORT) -> None:
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        addr = (address, port)
        self._socket.bind(addr)
        logger.debug(f"Bound to ({addr})")

    def __enter__(self) -> 'SocketServer':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.shutdown()

    def run(self) -> None:
        """Runs the server.

        Starts listening the socket in the endless loop, accepts connections,
        manages connections' graceful closing, calls connection handler for
        each connect.
        """
        while True:
            self._socket.listen(self.MAX_CONNECTIONS)
            try:
                conn, addr = self._socket.accept()
            except OSError:
                logger.exception("Failed to accept connection")
                continue

            logger.info(f'New connection from {addr}')
            with conn:
                try:
                    logger.debug(f'Handling connection from {addr}')
                    self.handle_connection(conn, addr)
                except ConnectionBrokenError:
                    logger.warning(f'Connection from {addr} has broken')
                except Exception:
                    logger.exception(f"Uncaught exception while handling connection from {addr}")
            logger.info(f"Closed connection from {addr}")

    def shutdown(self) -> None:
        """Shutdowns the socket"""
        logger.debug('Shutting down')
        self._socket.shutdown(socket.SHUT_RDWR)
        self._socket.close()
        logger.debug('Shut down')

    def handle_connection(self, conn: socket.socket, addr: tuple[str, int]) -> None:
        """Handles connection"""
        pass

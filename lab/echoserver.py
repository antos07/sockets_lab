import socket

from loguru import logger

from .socketserver import SocketServer


class EchoServer(SocketServer):
    """A simple blocking echo socket-server.

    Uses `socket.socket` as the low-level backend. Socket's family is `AF_INET`,
    its type is `SOCK_STREAM` (so it uses TCP), and its protocol is default.
    Binds socket to the given address (localhost by default) and
    the given port (`lab.constants.DEFAULT_PORT` is used by default).

    Support the context manager protocol. Exiting the context manager is
    equivalent to `shutdown()`.
    """

    def handle_connection(self, conn: socket.socket, addr: tuple[str, int]) -> None:
        while data := conn.recv(1024):
            logger.info(f'Received {data} from {addr}')
            conn.send(b'Ok')

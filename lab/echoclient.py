from .socketclient import SocketClient


class EchoClient(SocketClient):
    """A simple blocking input echo socket-client.

        Uses `socket.socket` as the low-level backend. Socket's family is `AF_INET`,
        its type is `SOCK_STREAM` (so it uses TCP), and its protocol is default. Connects
        to the socket with the given address (localhost by default) and the given
        port (`lab.constants.DEFAULT_PORT` is used by default).

        Support the context manager protocol. Exiting the context manager is
        equivalent to `disconnect()`."""

    def run(self):
        while text := input():
            self._socket.send(text.encode())
            print(self._socket.recv(1024).decode())

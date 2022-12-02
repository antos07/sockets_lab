import socket
from dataclasses import dataclass
from typing import Optional, Type, TypeVar

from loguru import logger

from . import constants
from .basecommand import BaseCommand
from .exceptions import UnrecognizedCommandError, ConnectionBrokenError
from .finishsessioncommand import FinishSessionCommand
from .isprimecommand import IsPrimeCommand
from .socketserver import SocketServer

__all__ = ['CommandServer']

from .whocommand import WhoCommand

_ExpectedCommandType = TypeVar('_ExpectedCommandType', bound=BaseCommand)


@dataclass(init=False)
class SessionData:
    author: str = constants.AUTHOR

    session_running: bool = True

    # implementing IsPrimeSessionData protocol
    numbers_cnt: int = 0
    primes_cnt: int = 0
    min_value: int = IsPrimeCommand.MAX_ALLOWED
    max_value: int = IsPrimeCommand.MIN_ALLOWED


class CommandServer(SocketServer):
    """A blocking socket-server that can respond to commands.

    Uses `socket.socket` as the low-level backend. Socket's family is `AF_INET`,
    its type is `SOCK_STREAM` (so it uses TCP), and its protocol is default.
    Binds socket to the given address (localhost by default) and
    the given port (`lab.constants.DEFAULT_PORT` is used by default).

    Support the context manager protocol. Exiting the context manager is
    equivalent to `shutdown()`.

    Supported commands:
    - isprime(n), on which server responds with bool(1) or bool(0)
    - who(), on which server responds with who(author)
    - finishsession(), on which server finishes current session and
      responds with stats(numbers_cnt, primes_cnt, min_number, max_number)
    """

    MESSAGE_HEADER_SIZE_LENGTH = 1
    RECV_BUFFER_SIZE = 256

    commands_decode_table: dict[str, BaseCommand] = {
        WhoCommand.name: WhoCommand,
        IsPrimeCommand.name: IsPrimeCommand,
        FinishSessionCommand.name: FinishSessionCommand
    }

    def __init__(self, address: str = constants.DEFAULT_HOST, port: int = constants.DEFAULT_PORT) -> None:
        super().__init__(address, port)
        self._buffer = bytes()

    def handle_connection(self, conn: socket.socket, addr: tuple[str, int]) -> None:
        session_data = SessionData()
        self._buffer = bytes()
        while session_data.session_running:
            logger.debug(f'Receiving command from {addr}')
            try:
                command = self._receive_message(conn)
            except UnrecognizedCommandError as e:
                logger.warning(f'Skipping command due to "{e}"')
                continue
            logger.info(f"Received '{command}' from {addr}")
            if not command:
                continue

            logger.debug(f'Executing command {command} on session_data {session_data}')
            response_command = command(session_data)
            logger.debug(f'Execution command {command} set session_data to {session_data}')

            logger.debug(f'Sending response {response_command} to {addr}')
            self._send_command(conn, response_command)
            logger.info(f'Sent response {response_command} to {addr}')

    def _receive_message(self, conn: socket.socket) -> Optional[BaseCommand]:
        """Receives message and decodes it into command"""
        logger.debug('Receiving header length')
        header_length = int.from_bytes(self._recv(conn, self.MESSAGE_HEADER_SIZE_LENGTH), byteorder='little')
        logger.debug(f'{header_length=}')
        if header_length == self.MESSAGE_HEADER_SIZE_LENGTH:
            return

        logger.debug('Receiving command name')
        try:
            command_name = self._recv(conn, header_length - self.MESSAGE_HEADER_SIZE_LENGTH).decode()
        except UnicodeDecodeError:
            raise UnrecognizedCommandError('Could not decode command name')
        logger.debug(f'{command_name=}')
        try:
            command_type = self.commands_decode_table[command_name]
        except KeyError:
            raise UnrecognizedCommandError(f'Command with name "{command_name}" is not in commands_decode_table')
        logger.debug('Receiving command data')
        command_data = self._recv(conn, command_type.data_length)
        logger.debug(f'{command_data=}')
        return command_type.from_bytes(command_data)

    def _send_command(self, conn: socket.socket, command: BaseCommand) -> None:
        """Encodes command and sends it as a message"""
        try:
            encoded_command_name = command.name.encode()
        except UnicodeEncodeError:
            raise UnrecognizedCommandError(f'Could not encode "{command.name}"')
        header_length = self.MESSAGE_HEADER_SIZE_LENGTH + len(encoded_command_name)
        header = header_length.to_bytes(self.MESSAGE_HEADER_SIZE_LENGTH, 'little') + encoded_command_name
        data = bytes(command)
        message = header + data
        self._send(conn, message)

    def _recv(self, conn: socket.socket, n: int) -> bytes:
        """Wrapper for _scoket.recv"""
        while len(self._buffer) < n:
            buffer = conn.recv(self.RECV_BUFFER_SIZE)
            if not buffer:
                raise ConnectionBrokenError
            self._buffer += buffer
        result, self._buffer = self._buffer[:n], self._buffer[n:]
        return result

    def _send(self, conn: socket.socket, data: bytes) -> None:
        """Wrapper for _socket.sendall. Ensures all data was sent"""
        conn.sendall(data)

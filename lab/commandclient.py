import random
import re
import readline  # noqa
from enum import Enum
from functools import partial
from pathlib import Path
from typing import Callable, Iterator, TextIO, TypeVar, Type, Optional

from loguru import logger

from . import constants
from .basecommand import BaseCommand
from .boolcommand import BoolCommand
from .exceptions import ConnectionBrokenError, UnrecognizedCommandError
from .finishsessioncommand import FinishSessionCommand
from .isprimecommand import IsPrimeCommand
from .socketclient import SocketClient
from .statscommand import StatsCommand
from .whocommand import WhoCommand

__all__ = ['CommandClient']

_ExpectedCommandType = TypeVar('_ExpectedCommandType', bound=BaseCommand)


class ClientMode(Enum):
    GENERATE_NUMBERS = 1
    ENTER_NUMBERS = 2
    ENTER_COMMANDS = 3


class CommandClient(SocketClient):
    """Simplier implementation of CommandClient"""

    MESSAGE_HEADER_SIZE_LENGTH = 1
    RECV_BUFFER_SIZE = 256

    commands_decode_table: dict[str, BaseCommand] = {
        WhoCommand.name: WhoCommand,
        BoolCommand.name: BoolCommand,
        StatsCommand.name: StatsCommand
    }

    def __init__(self, output_file: Path, address: str = constants.DEFAULT_HOST,
                 port: int = constants.DEFAULT_PORT) -> None:
        super().__init__(address, port)
        self._buffer = bytes()
        self.output_file = output_file

    def run(self):
        modes = {
            ClientMode.GENERATE_NUMBERS: partial(self._filter_primes_mode, self._random_numbers_generator),
            ClientMode.ENTER_NUMBERS: partial(self._filter_primes_mode, self._input_numbers_generator),
            ClientMode.ENTER_COMMANDS: self._enter_commands_mode
        }
        mode = modes[self._choose_mode()]
        mode()

    def _choose_mode(self) -> ClientMode:
        prompt = (
            'Available modes:\n'
            f'{ClientMode.GENERATE_NUMBERS.value}) Filter 50 random numbers\n'
            f'{ClientMode.ENTER_NUMBERS.value}) Filter numbers entered by you\n'
            f'{ClientMode.ENTER_COMMANDS.value}) Execute raw commands\n'
            '\n'
            'Select the mode by entering its number: '
        )
        correct_input = False
        while not correct_input:
            mode = input(prompt)
            try:
                mode = ClientMode(int(mode))
            except ValueError:
                print('Incorrect input!')
            else:
                correct_input = True
        return mode  # noqa

    def _filter_primes_mode(self, numbers_generator: Callable[[], Iterator[int]]) -> None:
        self._print_author()
        with self.output_file.open('w') as output_file:
            self._filter_primes(numbers_generator, output_file)
        self._finish_session()

    def _enter_commands_mode(self) -> None:
        for command in self._commands_generator():
            logger.debug(f'Executing command {command}')
            self._send_command(command)
            response = self._receive_message()
            print(f'Server responded with {response}')

    def _print_author(self) -> None:
        self._send_command(WhoCommand())
        who_command = self._receive_command(WhoCommand)
        print(f'Author is: {who_command.author}')

    def _filter_primes(self, numbers_generator: Callable[[], Iterator[int]], output_file: TextIO) -> None:
        for n in numbers_generator():
            logger.debug(f'Checking whether {n} is prime')
            try:
                self._send_command(IsPrimeCommand(n))
            except OverflowError:
                print(f'{n} is too big')
                logger.warning(f'Skipped number {n} due to OverflowError')
                continue
            try:
                response_command = self._receive_command(BoolCommand)
            except TypeError:
                logger.warning(f'Skipping {n} due to an unexpected server response')
                continue
            if response_command.value:
                print(f'{n} is prime')
                logger.debug(f'{n} is prime. Writing to file')
                output_file.write(str(n) + '\n')
            else:
                print(f'{n} is not prime')
                logger.debug(f'{n} is not prime')

    def _finish_session(self) -> None:
        self._send_command(FinishSessionCommand())
        stats_command = self._receive_command(StatsCommand)
        print('Stats:')
        print(f'numbers_cnt={stats_command.numbers_cnt}',
              f'primes_cnt={stats_command.primes_cnt}',
              f'min_value={stats_command.min_value}',
              f'max_value={stats_command.max_value}')

    @staticmethod
    def _input_numbers_generator() -> Iterator[int]:
        while n := input('Enter number or skip to finish: '):
            try:
                yield int(n)
            except ValueError:
                print('Wrong input. Number expected')

    @staticmethod
    def _random_numbers_generator() -> Iterator[int]:
        n = 50
        for _ in range(n):
            yield random.randint(IsPrimeCommand.MIN_ALLOWED, IsPrimeCommand.MAX_ALLOWED)

    @staticmethod
    def _commands_generator() -> Iterator[BaseCommand]:
        prompt = (
            'Available commands: who(), isprime(n), finishsession().\n'
            'Enter command or press "Enter" to finish: '
        )
        while command := input(prompt).strip():
            if re.match(r'^who\W*\(\W*\)$', command):
                yield WhoCommand()
            elif m := re.match(r'isprime\W*\(\W*(-?\d+)\W*\)', command):
                n = int(m.group(1))
                yield IsPrimeCommand(n)
            elif re.match(r'^finishsession\W*\(\W*\)$', command):
                yield FinishSessionCommand()
            else:
                print('Unrecognized command!')

    def _receive_command(self, command_type: Type[_ExpectedCommandType]) -> _ExpectedCommandType:
        logger.debug('Receiving response from server')
        command = self._receive_message()
        logger.info(f"Received '{command}' from server")
        if not isinstance(command, command_type):
            logger.error(f'Received unexpected command {command}')
            raise TypeError
        return command

    def _receive_message(self) -> Optional[BaseCommand]:
        """Receives message and decodes it into command"""
        logger.debug('Receiving header length')
        header_length = int.from_bytes(self._recv(self.MESSAGE_HEADER_SIZE_LENGTH), byteorder='little')
        logger.debug(f'{header_length=}')
        if header_length == self.MESSAGE_HEADER_SIZE_LENGTH:
            return

        logger.debug('Receiving command name')
        try:
            command_name = self._recv(header_length - self.MESSAGE_HEADER_SIZE_LENGTH).decode()
        except UnicodeDecodeError:
            raise UnrecognizedCommandError('Could not decode command name')
        logger.debug(f'{command_name=}')
        try:
            command_type = self.commands_decode_table[command_name]
        except KeyError:
            raise UnrecognizedCommandError(f'Command with name "{command_name}" is not in commands_decode_table')
        logger.debug('Receiving command data')
        command_data = self._recv(command_type.data_length)
        logger.debug(f'{command_data=}')
        return command_type.from_bytes(command_data)

    def _send_command(self, command: BaseCommand) -> None:
        """Encodes command and sends it as a message"""
        logger.debug(f'Sending command "{command}"')
        try:
            encoded_command_name = command.name.encode()
        except UnicodeEncodeError:
            raise UnrecognizedCommandError(f'Could not encode "{command.name}"')
        header_length = self.MESSAGE_HEADER_SIZE_LENGTH + len(encoded_command_name)
        header = header_length.to_bytes(self.MESSAGE_HEADER_SIZE_LENGTH, 'little') + encoded_command_name
        data = bytes(command)
        message = header + data
        self._send(message)
        logger.info(f'Sent command "{command}" to server')

    def _recv(self, n: int) -> bytes:
        """Wrapper for _scoket.recv"""
        while len(self._buffer) < n:
            buffer = self._socket.recv(self.RECV_BUFFER_SIZE)
            if not buffer:
                raise ConnectionBrokenError
            self._buffer += buffer
        result, self._buffer = self._buffer[:n], self._buffer[n:]
        return result

    def _send(self, data: bytes) -> None:
        """Wrapper for _socket.sendall. Ensures all data was sent"""
        self._socket.sendall(data)

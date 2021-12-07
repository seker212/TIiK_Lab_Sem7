from io import TextIOWrapper
import logging
from os import read
from typing import Optional, Tuple

SEARCH_BUFFER_BIT_SIZE: int = 4
LOOK_AHEAD_BUFFER_BIT_SIZE: int = 4
ENCODING_CHAR_BYTE_SIZE: int = 1

class Compressor:
    def __init__(self, source: str, target: str) -> None:
        self.source_file: TextIOWrapper = open(source, 'r') #TODO: Add setting up encoding as param
        logging.debug('Source file opened')
        self.target = target #TODO: change target if file exists
        self.search_buffer: str = ''
        logging.debug(f'Initiated search buffer: \'{self.search_buffer}\' (Len: {len(self.search_buffer)})')
        self.look_ahead_buffer: str = self.source_file.read(pow(2, LOOK_AHEAD_BUFFER_BIT_SIZE))
        logging.debug(f'Initiated look ahead buffer: \'{self.look_ahead_buffer}\' (Len: {len(self.look_ahead_buffer)})')

    def __del__(self):
        self.source_file.close()
        logging.debug('Source file closed')

    def _move_buffers(self, lenght: int) -> None:
        self.search_buffer = self.search_buffer + self.look_ahead_buffer[:lenght]
        if len(self.search_buffer) > pow(2, SEARCH_BUFFER_BIT_SIZE):
            self.search_buffer = self.search_buffer[len(self.search_buffer) - pow(2, SEARCH_BUFFER_BIT_SIZE):]
        logging.debug(f'Search buffer moved by {lenght}. New value: \'{self.search_buffer}\' (Len: {len(self.search_buffer)})')
        self.look_ahead_buffer = self.look_ahead_buffer[lenght:] + self.source_file.read(lenght)
        logging.debug(f'Look ahead buffer moved by {lenght}. New value: \'{self.look_ahead_buffer}\' (Len: {len(self.look_ahead_buffer)})')

    def _new_block(self) -> Tuple[Tuple[int, int, str], int]:
        prev_find_index: Optional[int] = None
        find_index: Optional[int] = None
        
        for substring_len in range(len(self.look_ahead_buffer)+1):
            if substring_len > 0:
                prev_find_index = find_index
            logging.debug(f'Searching for substring: \'{self.look_ahead_buffer[:substring_len]}\' (substring_len = {substring_len})')
            find_index = self.search_buffer.find(self.look_ahead_buffer[:substring_len])
            if find_index == -1 or substring_len == len(self.look_ahead_buffer):
                logging.debug(f'Substring not found.')
                if substring_len == 1:
                    logging.debug(f'Returning: (0, 0, \'{self.look_ahead_buffer[0]}\'), substring_len = {substring_len}')
                    return ((0, 0, self.look_ahead_buffer[0]), substring_len)
                else:
                    logging.debug(f'Returning: ({len(self.search_buffer)-prev_find_index}, {substring_len-1}, \'{self.look_ahead_buffer[substring_len-1]}\')')
                    return ((len(self.search_buffer)-prev_find_index, substring_len-1, self.look_ahead_buffer[substring_len-1]), substring_len)
            else:
                logging.debug(f'Substring found. find_index= {find_index}')
    
    def compress(self) -> bytes:
        logging.info('Started encoding to blocks')
        result: bytes = b''
        while len(self.look_ahead_buffer) > 0: #TODO: Change source to file
            block, move_len = self._new_block()
            binary = self._block_to_bytes(block)
            result += binary
            with open(self.target, 'ab+') as target_file:
                target_file.write(binary)
            self._move_buffers(move_len)
        logging.info('Encoded to blocks')
        return result

    def _number_to_bitstr(self, value: int, str_len: int):
        binstr: str = "{0:08b}".format(value)[-str_len:]
        if len(binstr) < str_len:
            binstr = '0'*(str_len-len(binstr)) + binstr
        return binstr
    
    def _block_to_bytes(self, block: Tuple[int, int, str]) -> bytes:
        len_binstr = self._number_to_bitstr(block[0], SEARCH_BUFFER_BIT_SIZE)
        offset_binstr = self._number_to_bitstr(block[1], LOOK_AHEAD_BUFFER_BIT_SIZE)
        char_binstr = self._number_to_bitstr(ord(block[2]), 8*ENCODING_CHAR_BYTE_SIZE)
        binstr = len_binstr + offset_binstr + char_binstr
        return bytes([int(binstr[i:i+8], 2) for i in range(0, len(binstr), 8)])

if __name__ == '__main__':
    logging.basicConfig(level=logging.NOTSET, format='%(levelname)s:\t%(message)s')
    if (SEARCH_BUFFER_BIT_SIZE + LOOK_AHEAD_BUFFER_BIT_SIZE) % 8 != 0:
        logging.error('Sum of buffers\' sizes isn\'t divisible by 8')
    else:
        c = Compressor('input.txt', 'output.lz77')
        result = c.compress()
        print('\n==============')
        print(result.hex())
        print(result.hex() == '00000000610000000062110000006342000000637400000061')
        print(result.hex() == '00610062116342637461')
        print('==============\n')

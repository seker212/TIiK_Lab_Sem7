import os

from io import TextIOWrapper
import logging
from typing import Optional, Tuple

SEARCH_BUFFER_BIT_SIZE: int = 4
LOOK_AHEAD_BUFFER_BIT_SIZE: int = 4
ENCODING_CHAR_BYTE_SIZE: int = 1

def number_to_bitstr(value: int, str_len: int):
    binstr: str = "{0:08b}".format(value)[-str_len:]
    if len(binstr) < str_len:
        binstr = '0'*(str_len-len(binstr)) + binstr
    return binstr

class Compressor:
    def __init__(self, source: str, target: str) -> None:
        logging.debug('Initializing compressor')
        self.source_file: TextIOWrapper = open(source, 'r') #TODO: Add setting up encoding as param
        logging.debug('Compression source file opened')
        self.target = target #TODO: change target if file exists
        self.search_buffer: str = ''
        logging.debug(f'Initiated search buffer: \'{self.search_buffer}\' (Len: {len(self.search_buffer)})')
        self.look_ahead_buffer: str = self.source_file.read(pow(2, LOOK_AHEAD_BUFFER_BIT_SIZE)-1)
        logging.debug(f'Initiated look ahead buffer: \'{self.look_ahead_buffer}\' (Len: {len(self.look_ahead_buffer)})')

    def __del__(self):
        self.source_file.close()
        logging.debug('Compression source file closed')

    def _move_buffers(self, lenght: int) -> None:
        self.search_buffer += self.look_ahead_buffer[:lenght]
        if len(self.search_buffer) > pow(2, SEARCH_BUFFER_BIT_SIZE) - 1:
            self.search_buffer = self.search_buffer[len(self.search_buffer) - (pow(2, SEARCH_BUFFER_BIT_SIZE) - 1):]
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
        while len(self.look_ahead_buffer) > 0:
            block, move_len = self._new_block()
            binary = self._block_to_bytes(block)
            with open(self.target, 'ab+') as target_file:
                target_file.write(binary)
            self._move_buffers(move_len)
        logging.info('End of compression')
    
    def _block_to_bytes(self, block: Tuple[int, int, str]) -> bytes:
        len_binstr = number_to_bitstr(block[0], SEARCH_BUFFER_BIT_SIZE)
        offset_binstr = number_to_bitstr(block[1], LOOK_AHEAD_BUFFER_BIT_SIZE)
        char_binstr = number_to_bitstr(ord(block[2]), 8*ENCODING_CHAR_BYTE_SIZE)
        binstr = len_binstr + offset_binstr + char_binstr
        logging.debug(f'Encoded ({block[0]}, {block[1]}, \'{block[2]}\') as \'{binstr}\'')
        return bytes([int(binstr[i:i+8], 2) for i in range(0, len(binstr), 8)])

class Decompressor:
    def __init__(self, source: str, target: str) -> None:
        self.source_file: TextIOWrapper = open(source, 'rb') #TODO: Add setting up encoding as param
        logging.debug('Decompression source file opened')
        self.target = target #TODO: change target if file exists
        self.search_buffer: str = ''

    def __del__(self):
        self.source_file.close()
        logging.debug('Decompression source file closed')

    def _move_buffer(self, value: str) -> None:
        self.search_buffer += value
        if len(self.search_buffer) > pow(2, SEARCH_BUFFER_BIT_SIZE) - 1:
            self.search_buffer = self.search_buffer[len(self.search_buffer) - (pow(2, SEARCH_BUFFER_BIT_SIZE) - 1):]
        logging.debug(f'Moved search buffer. Appended value: \'{value}\'. New buffer value: \'{self.search_buffer}\' (Len: {len(self.search_buffer)})')

    def _read_block(self) -> Optional[Tuple[int, int, str]]:
        block_lo_bin: bytes = self.source_file.read(int((SEARCH_BUFFER_BIT_SIZE + LOOK_AHEAD_BUFFER_BIT_SIZE)/8))
        if len(block_lo_bin) == 0:
            logging.debug('Reached end of file')
            return None
        lenght_offset_binstr: str = number_to_bitstr(int.from_bytes(block_lo_bin, byteorder='big', signed=False), SEARCH_BUFFER_BIT_SIZE + LOOK_AHEAD_BUFFER_BIT_SIZE)
        logging.debug(f'Read length and offset binary: {lenght_offset_binstr}')
        length: int = int(lenght_offset_binstr[:SEARCH_BUFFER_BIT_SIZE], 2)
        offset: int = int(lenght_offset_binstr[SEARCH_BUFFER_BIT_SIZE:], 2)
        char: str = chr(int.from_bytes(self.source_file.read(ENCODING_CHAR_BYTE_SIZE), byteorder='big', signed=False))
        logging.debug(f'Returning new block: ({length}, {offset}, \'{char}\')')
        return (length, offset, char)

    def decompress(self) -> None:
        logging.info('Starting decompression')
        while True:
            block = self._read_block()
            if block is None:
                logging.info('Ending decompression')
                break
            if block[0] == 0 and block[1] == 0:
                with open(self.target, 'a') as target_file:
                    target_file.write(block[2]) 
                    logging.debug(f'Appended to file: \'{block[2]}\' (Len: {len(block[2])})')
                self.search_buffer += block[2]
            else:
                substring: str = self.search_buffer[len(self.search_buffer) - block[0]:len(self.search_buffer) - block[0] + block[1]]
                with open(self.target, 'a') as target_file:
                    target_file.write(substring + block[2])
                    logging.debug(f'Appended to file: \'{substring + block[2]}\' (Len: {len(block[2])})')
                self.search_buffer += substring + block[2]
            if len(self.search_buffer) > pow(2, SEARCH_BUFFER_BIT_SIZE) - 1:
                self.search_buffer = self.search_buffer[len(self.search_buffer) - (pow(2, SEARCH_BUFFER_BIT_SIZE) - 1):]
            logging.debug(f'Updated search buffer. New value: \'{self.search_buffer}\' (Len: {len(self.search_buffer)})')


if __name__ == '__main__':
    if os.path.exists("log.log"):
        os.remove("log.log")

    logging.basicConfig(filename='log.log', level=logging.NOTSET, format='%(levelname)s:\t%(message)s')
    if (SEARCH_BUFFER_BIT_SIZE + LOOK_AHEAD_BUFFER_BIT_SIZE) % 8 != 0:
        logging.error('Sum of buffers\' sizes isn\'t divisible by 8')
    else:

        if os.path.exists("output.lz77"):
            os.remove("output.lz77")

        c = Compressor('input.txt', 'output.lz77')
        result = c.compress()
        
        if os.path.exists("output.txt"):
            os.remove("output.txt")
        
        d = Decompressor('output.lz77', 'output.txt')
        d.decompress()

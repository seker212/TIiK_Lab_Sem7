import os

from io import TextIOWrapper
import logging
from typing import Optional, Tuple
from sys import argv, stdout

SEARCH_BUFFER_BIT_SIZE: int = 4
LOOK_AHEAD_BUFFER_BIT_SIZE: int = 4
ENCODING_CHAR_BYTE_SIZE: int = 2

def number_to_bitstr(value: int, str_len: int):
    binstr: str = "{0:08b}".format(value)[-str_len:]
    if len(binstr) < str_len:
        binstr = '0'*(str_len-len(binstr)) + binstr
    return binstr

class Compressor:
    def __init__(self, source: str, target: str) -> None:
        logging.debug('Initializing compressor')
        with open(source, 'r') as source_file:
            self.search_buffer: str = source_file.read(1) * (pow(2, SEARCH_BUFFER_BIT_SIZE) - 1)
            with open(target, 'wb') as target_file:
                binary_int = number_to_bitstr(ord(self.search_buffer[0]), 8*ENCODING_CHAR_BYTE_SIZE)
                target_file.write(bytes([int(binary_int[i:i+8], 2) for i in range(0, len(binary_int), 8)]))
        logging.debug('Initiated search buffer: \'{0}\' (Len: {1})'.format(self.search_buffer.replace('\n', '\\n'), len(self.search_buffer)))
        self.source_file: TextIOWrapper = open(source, 'r') #TODO: Add setting up encoding as param
        logging.debug('Compression source file opened')
        self.target = target #TODO: change target if file exists
        self.look_ahead_buffer: str = self.source_file.read(pow(2, LOOK_AHEAD_BUFFER_BIT_SIZE)-1)
        logging.debug('Initiated look ahead buffer: \'{0}\' (Len: {1})'.format(self.look_ahead_buffer.replace('\n', '\\n'), len(self.look_ahead_buffer)))

    def __del__(self):
        self.source_file.close()
        # logging.debug('Compression source file closed')

    def _move_buffers(self, lenght: int) -> None:
        self.search_buffer += self.look_ahead_buffer[:lenght]
        if len(self.search_buffer) > pow(2, SEARCH_BUFFER_BIT_SIZE) - 1:
            self.search_buffer = self.search_buffer[len(self.search_buffer) - (pow(2, SEARCH_BUFFER_BIT_SIZE) - 1):]
        logging.debug('Search buffer moved by {0}. New value: \'{1}\' (Len: {2})'.format(lenght, self.search_buffer.replace('\n', '\\n'), len(self.search_buffer)))
        self.look_ahead_buffer = self.look_ahead_buffer[lenght:] + self.source_file.read(lenght)
        logging.debug('Look ahead buffer moved by {0}. New value: \'{1}\' (Len: {2})'.format(lenght, self.look_ahead_buffer.replace('\n', '\\n'), len(self.look_ahead_buffer)))

    def _new_block(self) -> Tuple[Tuple[int, int, str], int]:
        prev_find_index: Optional[int] = None
        find_index: Optional[int] = None
        
        for substring_len in range(len(self.look_ahead_buffer)+1):
            if substring_len > 0:
                prev_find_index = find_index
            logging.debug('Searching for substring: \'{0}\' (substring_len = {1})'.format(self.look_ahead_buffer[:substring_len].replace('\n', '\\n'), substring_len))
            find_index = self.search_buffer.find(self.look_ahead_buffer[:substring_len])
            if find_index == -1 or substring_len == len(self.look_ahead_buffer):
                logging.debug('Substring not found.')
                if substring_len == 1:
                    logging.debug('Returning: (0, 0, \'{0}\'), substring_len = {1}'.format(self.look_ahead_buffer[0].replace('\n', '\\n'), substring_len))
                    return ((0, 0, self.look_ahead_buffer[0]), substring_len)
                else:
                    logging.debug('Returning: ({0}, {1}, \'{2}\')'.format(prev_find_index, substring_len-1, self.look_ahead_buffer[substring_len-1].replace('\n', '\\n')))
                    return ((prev_find_index, substring_len-1, self.look_ahead_buffer[substring_len-1]), substring_len)
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
        offset_binstr = number_to_bitstr(block[0], SEARCH_BUFFER_BIT_SIZE)
        length_binstr = number_to_bitstr(block[1], LOOK_AHEAD_BUFFER_BIT_SIZE)
        char_binstr = number_to_bitstr(ord(block[2]), 8*ENCODING_CHAR_BYTE_SIZE)
        binstr = offset_binstr + length_binstr + char_binstr
        logging.debug('Encoded ({0}, {1}, \'{2}\') as \'{3}\''.format(block[0], block[1], block[2].replace('\n', '\\n'), binstr))
        return bytes([int(binstr[i:i+8], 2) for i in range(0, len(binstr), 8)])


#########################################################################
#########################################################################


class Decompressor:
    def __init__(self, source: str, target: str) -> None:
        self.source_file: TextIOWrapper = open(source, 'rb') #TODO: Add setting up encoding as param
        logging.debug('Decompression source file opened')
        self.search_buffer: str = chr(int.from_bytes(self.source_file.read(ENCODING_CHAR_BYTE_SIZE), byteorder='big', signed=False)) * (pow(2, SEARCH_BUFFER_BIT_SIZE) - 1)
        logging.debug('Initiated search buffer: \'{0}\' (Len: {1})'.format(self.search_buffer.replace('\n', '\\n'), len(self.search_buffer)))
        self.target = target #TODO: change target if file exists

    def __del__(self):
        self.source_file.close()
        # logging.debug('Decompression source file closed')

    def _move_buffer(self, value: str) -> None:
        self.search_buffer += value
        if len(self.search_buffer) > pow(2, SEARCH_BUFFER_BIT_SIZE) - 1:
            self.search_buffer = self.search_buffer[len(self.search_buffer) - (pow(2, SEARCH_BUFFER_BIT_SIZE) - 1):]
        logging.debug('Moved search buffer. Appended value: \'{0}\'. New buffer value: \'{1}\' (Len: {len(self.search_buffer)})'.replace(value.replace('\n', '\\n'), self.search_buffer.replace('\n', '\\n')))

    def _read_block(self) -> Optional[Tuple[int, int, str]]:
        block_lo_bin: bytes = self.source_file.read(int((SEARCH_BUFFER_BIT_SIZE + LOOK_AHEAD_BUFFER_BIT_SIZE)/8))
        if len(block_lo_bin) == 0:
            logging.debug('Reached end of file')
            return None
        offset_lenght_binstr: str = number_to_bitstr(int.from_bytes(block_lo_bin, byteorder='big', signed=False), SEARCH_BUFFER_BIT_SIZE + LOOK_AHEAD_BUFFER_BIT_SIZE)
        logging.debug(f'Read offset and length binary: {offset_lenght_binstr}')
        offset: int = int(offset_lenght_binstr[:SEARCH_BUFFER_BIT_SIZE], 2)
        lenght: int = int(offset_lenght_binstr[SEARCH_BUFFER_BIT_SIZE:], 2)
        char: str = chr(int.from_bytes(self.source_file.read(ENCODING_CHAR_BYTE_SIZE), byteorder='big', signed=False))
        logging.debug('Returning new block: ({0}, {1}, \'{2}\')'.format(offset, lenght, char.replace('\n', '\\n')))
        return (offset, lenght, char)

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
                    logging.debug('Appended to file: \'{0}\' (Len: {1})'.format(block[2].replace('\n', '\\n'), len(block[2])))
                self.search_buffer += block[2]
            else:
                substring: str = self.search_buffer[block[0]:block[0] + block[1]]
                with open(self.target, 'a') as target_file:
                    target_file.write(substring + block[2])
                    logging.debug('Appended to file: \'{0}\' (Len: {1})'.format((substring + block[2]).replace('\n', '\\n'), len(block[2])))
                self.search_buffer += substring + block[2]
            if len(self.search_buffer) > pow(2, SEARCH_BUFFER_BIT_SIZE) - 1:
                self.search_buffer = self.search_buffer[len(self.search_buffer) - (pow(2, SEARCH_BUFFER_BIT_SIZE) - 1):]
            logging.debug('Updated search buffer. New value: \'{0}\' (Len: {1})'.format(self.search_buffer.replace('\n', '\\n'), len(self.search_buffer)))


if __name__ == '__main__':
    filesnames = {
        'log_file': "log.log",
        'input': "input.txt",
        'compression_output': 'output.lz77',
        'decompression_output': 'output.txt'
    }

    if os.path.exists(filesnames['log_file']):
        os.remove(filesnames['log_file'])

    file_handler = logging.FileHandler(filename=filesnames['log_file'])
    file_handler.setLevel(logging.DEBUG)
    stdout_handler = logging.StreamHandler(stdout)
    stdout_handler.setLevel(logging.INFO)
    handlers = [file_handler, stdout_handler]
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:\t%(message)s', handlers=handlers)


    if (SEARCH_BUFFER_BIT_SIZE + LOOK_AHEAD_BUFFER_BIT_SIZE) % 8 != 0:
        logging.error('Sum of buffers\' sizes isn\'t divisible by 8')
    else:
        if '-c' in argv:
            if not os.path.exists(filesnames['input']):
                logging.error(f'Compression input file {filesnames["input"]} does not exist')
            else:
                if os.path.exists(filesnames['compression_output']):
                    os.remove(filesnames['compression_output'])

                c = Compressor(filesnames['input'], filesnames['compression_output'])
                result = c.compress()
        
        if '-d' in argv:
            if not os.path.exists(filesnames['compression_output']):
                logging.error(f'Decompression input file {filesnames["compression_output"]} does not exist')
            else:
                if os.path.exists(filesnames['decompression_output']):
                    os.remove(filesnames['decompression_output'])
                
                d = Decompressor(filesnames["compression_output"], filesnames['decompression_output'])
                d.decompress()

        if not (('-c' in argv) or ('-d' in argv)):
            logging.error('You must provide -c or -d option.')

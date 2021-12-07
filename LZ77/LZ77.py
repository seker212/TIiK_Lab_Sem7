import logging
from typing import Optional, Tuple

SEARCH_BUFFER_BIT_SIZE: int = 4
LOOK_AHEAD_BUFFER_BIT_SIZE: int = 4
ENCODING_CHAR_BYTE_SIZE: int = 1

class Compressor:
    def __init__(self, source: str, target: str) -> None:
        self.ptr: int = 0
        self.source = source #TODO: Change source to file
        self.target = target
        self.search_buffer: Optional[str] = None
        self.look_ahead_buffer: Optional[str] = None

    def _set_search_buffer(self) -> None: #TODO: Change to reading from file
        search_buffer_begin = None
        if self.ptr-pow(2, SEARCH_BUFFER_BIT_SIZE) < 0:
            search_buffer_begin = 0
        else:
            search_buffer_begin = self.ptr-pow(2, SEARCH_BUFFER_BIT_SIZE)
        self.search_buffer = self.source[search_buffer_begin:self.ptr]
        logging.debug(f'Search buffer set to: \'{self.search_buffer}\' (Len: {len(self.search_buffer)})')
    
    def _set_look_ahead_buffer(self) -> None: #TODO: Change to reading from file
        self.look_ahead_buffer = self.source[self.ptr:self.ptr+pow(2, LOOK_AHEAD_BUFFER_BIT_SIZE)]
        logging.debug(f'Look ahead buffer set to: \'{self.search_buffer}\' (Len: {len(self.search_buffer)})')

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
        while self.ptr < len(self.source): #TODO: Change source to file
            logging.debug(f'ptr_search: {self.ptr}')
            self._set_search_buffer()
            self._set_look_ahead_buffer()
            block, move_ptr = self._new_block()
            binary = self._block_to_bytes(block)
            
            result += binary
            with open(self.target, 'ab+') as target_file:
                target_file.write(binary)

            self.ptr += move_ptr
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
        string: str = 'abbcabcabbca'
        c = Compressor(string, 'output.lz77')
        result = c.compress()
        print('\n==============')
        print(result.hex())
        print(result.hex() == '00000000610000000062110000006342000000637400000061')
        print(result.hex() == '00610062116342637461')
        print('==============\n')

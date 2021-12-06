import logging
from typing import List, Optional, Tuple

#TODO: Assert that sum of buffers' sizes is divisible by 8
SEARCH_BUFFER_SIZE: int = 9
LOOK_AHEAD_BUFFER_SIZE: int = 7

class EncryptBuffer:
    def __init__(self, source: str) -> None:
        self.ptr: int = 0
        self.source = source #TODO: Change source to file
        self.search_buffer: Optional[str] = None
        self.look_ahead_buffer: Optional[str] = None

    def _set_search_buffer(self) -> None: #TODO: Change to reading from file
        search_buffer_begin = None
        if self.ptr-SEARCH_BUFFER_SIZE < 0:
            search_buffer_begin = 0
        else:
            search_buffer_begin = self.ptr-SEARCH_BUFFER_SIZE
        self.search_buffer = self.source[search_buffer_begin:self.ptr]
        logging.debug(f'Search buffer set to: \'{self.search_buffer}\' (Len: {len(self.search_buffer)})')
    
    def _set_look_ahead_buffer(self) -> None: #TODO: Change to reading from file
        self.look_ahead_buffer = self.source[self.ptr:self.ptr+LOOK_AHEAD_BUFFER_SIZE]
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
    
    def encode_to_blocks(self) -> List[Tuple[int, int, str]]:
        logging.info('Started encoding to blocks')
        result_list: List[Tuple[int, int, str]] = []
        while self.ptr < len(self.source): #TODO: Change source to file
            logging.debug(f'ptr_search: {self.ptr}')
            self._set_search_buffer()
            self._set_look_ahead_buffer()
            block, move_ptr = self._new_block()
            self.ptr += move_ptr
            result_list.append(block)
            logging.debug(f'Block list: {result_list}')
        logging.info('Encoded to blocks')
        return result_list

if __name__ == '__main__':
    logging.basicConfig(level=logging.NOTSET, format='%(levelname)s:\t%(message)s')
    if (SEARCH_BUFFER_SIZE + LOOK_AHEAD_BUFFER_SIZE) % 8 != 0:
        logging.error('Sum of buffers\' sizes isn\'t divisible by 8')
    string: str = 'abbcabcabbca'
    result = EncryptBuffer(string).encode_to_blocks()
    print('\n==============')
    print(result)
    print('==============')

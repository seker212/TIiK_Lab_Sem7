import logging

#TODO: Assert that sum of buffers' sizes is divisible by 8
SEARCH_BUFFER_SIZE: int = 9
LOOK_AHEAD_BUFFER_SIZE: int = 7

def encrypt(string:str):
    ptr_search: int = 0

    while ptr_search < len(string):
        logging.debug(f'ptr_search: {ptr_search}')
        search_buffer_begin = None
        if ptr_search-SEARCH_BUFFER_SIZE < 0:
            search_buffer_begin = 0
        else:
            search_buffer_begin = ptr_search-SEARCH_BUFFER_SIZE
        logging.debug(f'search_buffer_begin: {search_buffer_begin}')
        search_buffer: str = string[search_buffer_begin:ptr_search]
        ahead_buffer: str = string[ptr_search:ptr_search+LOOK_AHEAD_BUFFER_SIZE]
        logging.debug(f'Buffers: {search_buffer}\t{len(search_buffer)}\t\t{ahead_buffer}\t{len(ahead_buffer)}')
        substring_len = None
        prev_find_index = None
        find_index = None
        for i in range(len(ahead_buffer)+1):
            if i > 0:
                prev_find_index = find_index
            logging.debug(f'Searching for substring: \'{ahead_buffer[:i]}\' ({i})')
            find_index = search_buffer.find(ahead_buffer[:i])
            if find_index == -1 or i == len(ahead_buffer):
                logging.debug(f'Substring not found.')
                substring_len = i
                if i == 1:
                    logging.info(f'(0, 0, \'{ahead_buffer[0]}\')')
                else:
                    logging.info(f'({len(search_buffer)-prev_find_index}, {substring_len-1}, \'{ahead_buffer[substring_len-1]}\')')
                break
            else:
                logging.debug(f'Substring found. find_index= {find_index}')
        print()
        ptr_search += substring_len

if __name__ == '__main__':
    logging.basicConfig(level=logging.NOTSET, format='%(levelname)s:\t%(message)s')
    string: str = 'abbcabcabbca'
    encrypt(string)
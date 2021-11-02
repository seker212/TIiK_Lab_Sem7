from math import log, log2
from sys import argv

def count_chars(file: str):
    char_dict = {}
    char_count = 0
    
    with open(file, mode='r', encoding = 'utf-8') as file:
        for line in file:
            for char in line:
                if char in char_dict:
                    char_dict[char] = char_dict[char] + 1
                else:
                    char_dict[char] = 1
                char_count += 1
    
    return char_dict, char_count

def count_information(char_dict: dict, char_count: int, information_unit: int) -> None:
    for char, count in char_dict.items():
        char_dict[char] = [count, log(1/(count/char_count), information_unit)]

def entropy(char_dict: dict, char_count: int) -> float:
    entropy_sum = 0
    for count in char_dict.values():
        p = count[0]/char_count
        entropy_sum += p * log2(1/p)
    return entropy_sum

def save_output(char_dict: dict, char_count: int, entropy: float, base_filename: str):
    filename = base_filename + '_output.md'
    with open(filename, 'w', encoding = 'utf-8') as file:
        file.writelines([f'Binary entropy: {entropy}\n\n', f'Total file character count: {char_count}\n\n'])
        file.writelines(['| Znak | Wystąpienia | Ilość informacji |\n', '| --- | --- | --- |\n'])
        for char, value in char_dict.items():
            if char == '\n':
                file.writelines([f'| NEW LINE | {value[0]} | {value[1]} |\n'])
            elif char == ' ':
                file.writelines([f'| SPACE | {value[0]} | {value[1]} |\n'])
            elif char == '\r':
                file.writelines([f'| CARRIAGE RETURN | {value[0]} | {value[1]} |\n'])
            elif char == '\t':
                file.writelines([f'| HORIZONTAL TAB | {value[0]} | {value[1]} |\n'])
            else:
                file.writelines([f'| {char} | {value[0]} | {value[1]} |\n'])

if __name__ == '__main__':
    for arg in argv[1:]:
        char_dict, char_count = count_chars(arg)
        count_information(char_dict, char_count, 2)
        ent = entropy(char_dict, char_count)
        save_output(char_dict, char_count, ent, arg)
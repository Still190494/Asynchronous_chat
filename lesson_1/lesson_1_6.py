# 6. Создать текстовый файл test_file.txt, заполнить его тремя строками: «сетевое
# программирование», «сокет», «декоратор». Проверить кодировку файла по умолчанию.
# Принудительно открыть файл в формате Unicode и вывести его содержимое.


with open('test_file.txt') as f_n:
    print(f_n)
f_n.close()


with open('test_file.txt', "r", encoding='utf-8') as f_n_1:
    for el_str in f_n_1:
        print(f'{el_str}\n')

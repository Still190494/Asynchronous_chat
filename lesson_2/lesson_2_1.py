# 1. Задание на закрепление знаний по модулю CSV. Написать скрипт, осуществляющий выборку
# определенных данных из файлов info_1.txt, info_2.txt, info_3.txt и формирующий новый
# «отчетный» файл в формате CSV. Для этого:
# a. Создать функцию get_data(), в которой в цикле осуществляется перебор файлов с
# данными, их открытие и считывание данных. В этой функции из считанных данных
# необходимо с помощью регулярных выражений извлечь значения параметров
# «Изготовитель системы», «Название ОС», «Код продукта», «Тип системы». Значения
# каждого параметра поместить в соответствующий список. Должно получиться четыре
# списка — например, os_prod_list, os_name_list, os_code_list, os_type_list. В этой же
# функции создать главный список для хранения данных отчета — например, main_data
# — и поместить в него названия столбцов отчета в виде списка: «Изготовитель
# системы», «Название ОС», «Код продукта», «Тип системы». Значения для этих
# столбцов также оформить в виде списка и поместить в файл main_data (также для
# каждого файла);
# b. Создать функцию write_to_csv(), в которую передавать ссылку на CSV-файл. В этой
# функции реализовать получение данных через вызов функции get_data(), а также
# сохранение подготовленных данных в соответствующий CSV-файл;
# c. Проверить работу программы через вызов функции write_to_csv().


import re
import csv


def get_data():
    file_list = ['info_1.txt', 'info_2.txt', 'info_3.txt']
    main_data = [['Изготовитель системы', 'Название ОС', 'Код продукта', 'Тип системы'], [], [],
                 []]   # «Главный список»
    os_prod_list = []  # «Изготовитель системы»
    os_name_list = []  # «Название ОС»
    os_code_list = []  # «Код продукта»
    os_type_list = []  # «Тип системы»
    for i in file_list:
        with open(i, encoding='cp1251') as file:
            data = file.read()
        os_prod = re.compile(r'Изготовитель системы:\s+([a-zA-Z]+)')
        os_prod_list.append(','.join(re.findall(os_prod, data)))
        os_name = re.compile(r'Название ОС:\s+([a-zA-Z0-9А-Яа-я\s\.]{1,})[\n]')
        os_name_list.append(','.join(re.findall(os_name, data)))
        os_code = re.compile(r'Код продукта:\s+([-0-9a-zA-Z]+)')
        os_code_list.append(','.join(re.findall(os_code, data)))
        os_type = re.compile(r'Тип системы:\s+([-0-9a-zA-Z\s]+)[\n]')
        os_type_list.append(','.join(re.findall(os_type, data)))
    for i in range(len(os_name_list)):
        main_data[i + 1].append(os_prod_list[i])
        main_data[i + 1].append(os_name_list[i])
        main_data[i + 1].append(os_code_list[i])
        main_data[i + 1].append(os_type_list[i])
    return main_data


def write_to_csv(file):
    main_data = get_data()
    with open(file, 'w', encoding='utf-8') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_NONNUMERIC)
        for i in main_data:
            writer.writerow(i)


write_to_csv('test.csv')

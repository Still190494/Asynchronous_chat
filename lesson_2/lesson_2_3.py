# 3. Задание на закрепление знаний по модулю yaml. Написать скрипт, автоматизирующий сохранение данных в файле YAML-формата. Для этого:
# Подготовить данные для записи в виде словаря, в котором первому ключу соответствует список, второму — целое число, третьему — вложенный словарь,
#  где значение каждого ключа — это целое число с юникод-символом, отсутствующим в кодировке ASCII (например, €);
# Реализовать сохранение данных в файл формата YAML — например, в файл file.yaml. При этом обеспечить стилизацию файла с помощью параметра default_flow_style,
#  а также установить возможность работы с юникодом: allow_unicode = True;
# Реализовать считывание данных из созданного файла и проверить, совпадают ли они с исходными.


import yaml


my_list_1 = ['samsung', 'apple', 'dell', 'lg']
quantity = 10
my_list_2 = {
    'samsung': '€100',
    'apple': '€200',
    'dell': '€300',
    'lg': '€400'
}
my_dict = {
    'item': my_list_1,
    'quantity': quantity,
    'price': my_list_2
}

with open('file_1.yaml', 'w', encoding='utf-8') as f_i:
    yaml.dump(my_dict, f_i, default_flow_style=False, allow_unicode=True)

with open("file_1.yaml", 'r', encoding='utf-8') as f_o:
    my_dict_new = yaml.load(f_o, Loader=yaml.SafeLoader)

print(my_dict == my_dict_new)

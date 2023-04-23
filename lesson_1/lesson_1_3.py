# 3. Определить, какие из слов «attribute», «класс», «функция», «type» невозможно записать в
# байтовом типе.


str_1 = 'attribute'
str_2 = 'класс'
str_3 = 'type'
str_4 = 'функция'


my_list = [str_1, str_2, str_3, str_4]


for i in my_list:
    try:
        print(bytes(i, 'ascii'))
    except UnicodeEncodeError:
        print(f'Ошибка - слово "{i}" - !кириллица!')

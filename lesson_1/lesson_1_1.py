# 1. Каждое из слов «разработка», «сокет», «декоратор» представить в строковом формате и
# проверить тип и содержание соответствующих переменных. Затем с помощью
# онлайн-конвертера преобразовать строковые представление в формат Unicode и также
# проверить тип и содержимое переменных.


str_1 = 'разработка'
str_2 = 'сокет'
str_3 = 'декоратор'

print (f'{str_1} {type(str_1)}\n{str_2} {type(str_2)}\n{str_3} {type(str_3)}\n')


ustr_1 = '\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430'
ustr_2 = '\u0441\u043e\u043a\u0435\u0442'
ustr_3 = '\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440'

print (f'{ustr_1} {type(ustr_1)}\n{ustr_2} {type(ustr_2)}\n{ustr_3} {type(ustr_3)}\n')

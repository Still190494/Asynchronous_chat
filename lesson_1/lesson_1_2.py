# 2. Каждое из слов «class», «function», «method» записать в байтовом типе без преобразования в
# последовательность кодов (не используя методы encode и decode) и определить тип,
# содержимое и длину соответствующих переменных.


bstr_1 = b'class'
bstr_2 = b'function'
bstr_3 = b'method'

print (f'{bstr_1} {type(bstr_1)}{len(bstr_1)}\n{bstr_2} {type(bstr_2)}{len(bstr_1)}\n{bstr_3} {type(bstr_3)}{len(bstr_1)}\n')

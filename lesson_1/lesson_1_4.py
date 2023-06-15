# 4. Преобразовать слова «разработка», «администрирование», «protocol», «standard» из
# строкового представления в байтовое и выполнить обратное преобразование (используя
# методы encode и decode).


my_list = ['разработка', 'администрирование', 'protocol', 'standard']
for i in my_list:
    encode_str = i.encode('utf-8')
    decode_str = encode_str.decode('utf-8')
    print(f'Байтовое представление - {encode_str}\nСтроковое представление - {decode_str}\n')

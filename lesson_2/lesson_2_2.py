# 2. Задание на закрепление знаний по модулю json. Есть файл orders в формате JSON с информацией о заказах. Написать скрипт, автоматизирующий его заполнение данными. Для этого:
# Создать функцию write_order_to_json(), в которую передается 5 параметров — товар (item), количество (quantity), цена (price), покупатель (buyer), дата (date).
#  Функция должна предусматривать запись данных в виде словаря в файл orders.json. При записи данных указать величину отступа в 4 пробельных символа;
# Проверить работу программы через вызов функции write_order_to_json() с передачей в нее значений каждого параметра. 


from datetime import date
import json

def write_order_to_json():
    current_date = str(date.today())
    item = input('Введите название товара: ')
    quantity = int(input('Введите колличество товара: '))
    price = int(input('Введите цену товара: '))
    buyer = input('Введите покупателя товара: ')
    my_dict = {
        'Item' : item,
        'Quantity' : quantity,
        'Price' : price,
        'Buyer' : buyer,
        'Date' : current_date
    }


    with open('orders.json', 'r', encoding='utf8') as f_o:
        data = json.load(f_o)

    with open('orders.json', 'w', encoding='utf8') as f_i:
        orders_list = data['orders']
        orders_list.append(my_dict)
        json.dump(data, f_i, indent=4)


write_order_to_json()
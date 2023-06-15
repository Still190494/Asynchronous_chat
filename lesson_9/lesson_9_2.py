# 2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
# Меняться должен только последний октет каждого адреса.
# По результатам проверки должно выводиться соответствующее сообщение.

from ipaddress import ip_address
from subprocess import PIPE, Popen


# i = '173.194.222.0'
# j = i.split('.')[3]
# print(j)


def host_range_ping():
    start = input('Введите IP: ')
    stop = int(input('Введите колличество адрессов: '))
    my_dict = {'Доступные узлы': "", 'Недоступные узлы': ""}
    host_list = []
    [host_list.append(str(ip_address(start) + x)) for x in range(int(stop))]
    for hostname in host_list:
        try:
            hostname = ip_address(hostname)
        except ValueError:
            pass
        response = Popen(f"ping {hostname} -n {1}", shell=False, stdout=PIPE)
        response.wait()
        if response.returncode == 0:
            my_dict['Доступные узлы'] += f"{str(hostname)}\n"
            print(hostname, '«Узел доступен»')
        else:
            my_dict['Недоступные узлы'] += f"{str(hostname)}\n"
            print(hostname, '«Узел недоступен»')
    return my_dict


if __name__ == "__main__":
    host_range_ping()

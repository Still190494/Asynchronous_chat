# 1. Написать функцию host_ping(), в которой с помощью утилиты ping будет проверяться доступность сетевых узлов.
# Аргументом функции является список, в котором каждый сетевой узел должен быть представлен именем хоста или ip-адресом.
# В функции необходимо перебирать ip-адреса и проверять их доступность с выводом соответствующего сообщения («Узел доступен», «Узел недоступен»).
# При этом ip-адрес сетевого узла должен создаваться с помощью функции ip_address().


from ipaddress import ip_address
from subprocess import PIPE, Popen

ip_list = ['google.com', '192.168.0.305', 'vk.com', '192.168.0.1']


def host_ping(my_ip_list):
    for hostname in ip_list:
        try:
            hostname = ip_address(hostname)
        except ValueError:
            pass
        response = Popen(f"ping {hostname}", shell=False, stdout=PIPE)
        response.wait()
        if response.returncode == 0:
            print(hostname, '«Узел доступен»')
        else:
            print(hostname, '«Узел недоступен»')


if __name__ == '__main__':
    host_ping(ip_list)

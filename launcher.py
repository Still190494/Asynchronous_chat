import subprocess

process = int(input("Введите нужное колличество запускаемых приложений: "))
subprocess.Popen('python data_server.py -p 7777 -a localhost', creationflags=subprocess.CREATE_NEW_CONSOLE)
for num in range(1, process + 1):
    subprocess.Popen(f'python data_client.py localhost 7777 -n test_{num}', creationflags=subprocess.CREATE_NEW_CONSOLE)

import logging
import sys
import os

curr_dir = os.getcwd()
log_dir = os.path.join(curr_dir, 'file_logs')
if not os.path.exists(log_dir):
    os.mkdir(log_dir)
logging_file = os.path.join(log_dir, 'client.log')

# Создание именованного логгера
log = logging.getLogger('client')

# Журналирование должно производиться в лог-файл;
log_file = logging.FileHandler(logging_file, encoding='utf8')

# Сообщения лога должны иметь следующий формат: "<дата-время> <уровеньважности> <имямодуля> <сообщение>";
formater = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

log_file.setLevel(logging.DEBUG)
log_file.setFormatter(formater)
critical_handler = logging.StreamHandler(sys.stderr)
critical_handler.setLevel(logging.CRITICAL)
critical_handler.setFormatter(formater)

log.addHandler(log_file)
log.addHandler(critical_handler)
log.setLevel(logging.DEBUG)

if __name__ == '__main__':
    log.critical('Критическая ошибка')
    log.error('Ошибка')
    log.debug('Отладочная информация')
    log.info('Информационное сообщение')

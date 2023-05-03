import logging
import sys


# Создание именованного логгера
log = logging.getLogger('client')

# Журналирование должно производиться в лог-файл;
log_file = log.addHandler(logging.FileHandler('client.log', encoding='utf8'))


# Сообщения лога должны иметь следующий формат: "<дата-время> <уровеньважности> <имямодуля> <сообщение>";
formater = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')



log_file.setLevel(logging.DEBUG)
log_file.setFormatter(formater)
critical_handler = log.addHandler(logging.StreamHandler(sys.stderr))
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
import logging
import sys
import traceback
import inspect



sys.setrecursionlimit(10000)

'''ДЕКОРАТОР @log'''
if sys.argv[0].find('client') == -1:
    logger = logging.getLogger('server')
else:
    logger = logging.getLogger('client')


def log(func):
    def log_save(*args,**kwargs):
        r = func(*args, **kwargs)
        logger.info(f'Была вызвана функция {func.__name__} c параметрами {args}, {kwargs}. '
                    f'Вызов из функции {inspect.stack()[1][3]}')
        return r
    return log_save


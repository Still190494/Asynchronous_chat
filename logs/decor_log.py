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


enable_tracing = True
def log(func):
    if enable_tracing:
        def log_save(*args,**kwargs):
            r = func(*args, **kwargs)
            logger.info(f'Была вызвана функция {func.__name__} c параметрами {args}, {kwargs}. '
                        f'Вызов из функции {inspect.stack()[1][3]}')
            return r
        return log_save
    else:
        return func

# def log(func_log):
#     def func_log(*args, **kwargs):
#         r = func_log(*args, **kwargs)
#         logger.info(f'Была вызвана функция {func_log.__name__} c аргументами {args}, {kwargs}. '
#                     f'Вызов из модуля {func_log.__module__}. Вызов из'
#                     f' функции {traceback.format_stack()[0].strip().split()[-1]}.'
#                     f'Вызов из функции {inspect.stack()[1][3]}')
#         return r
#     return func_log

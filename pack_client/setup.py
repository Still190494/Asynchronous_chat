from setuptools import setup, find_packages

setup(name="mess_client",
      version="0.1",
      description="mess_client",
      author="Artem",
      author_email="artem@yandex.ru",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )

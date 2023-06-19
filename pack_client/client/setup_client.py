import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["utils", "logs", "client", "sqlite3"],
}
setup(
    name="client_chat_pyqt_still190494_exe",
    version="0.1",
    description="client_chat_pyqt_still190494_exe",
    options={
        "build_exe": build_exe_options
    },
    executables=[Executable('data_client.py',
                            base='Win32GUI',
                            # targetName='data_client.exe',
                            )]
)
import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["utils", "logs", "server", "sqlite3"],
}
setup(
    name="server_chat_pyqt_still190494_exe",
    version="0.1",
    description="server_chat_pyqt_still190494_exe",
    options={
        "build_exe": build_exe_options
    },
    executables=[Executable('data_server.py',
                            base='Win32GUI',
                            # targetName='server.exe',
                            )]
)
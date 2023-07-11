from PyQt5.QtWidgets import QMainWindow

from .main import IPCMain
from .renderer import IPCRenderer


__all__ = [
    "CreateIPC"
]

def CreateIPC(window: QMainWindow) -> (IPCMain, IPCRenderer):
    """
    IPC对象生成器
    :param window: QMainWindow对象,也可以是loadUi返回的对象
    :return: ipcMain -> 任务IPC对象; ipcRenderer -> 渲染IPC对象
    """
    ipcMain = IPCMain(window)
    ipcRenderer = IPCRenderer(ipcMain)
    ipcMain.bind_quit()
    ipcMain.run()

    return ipcMain, ipcRenderer
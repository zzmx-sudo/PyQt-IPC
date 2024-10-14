from PyQt5.QtWidgets import QMainWindow

from .main import IPCMain
from .renderer import IPCRenderer
from .exception import OperationException


__all__ = [
    "CreateIPC"
]

def CreateIPC(
    window: QMainWindow,
    interval: int = 200
) -> (IPCMain, IPCRenderer):
    """
    IPC对象生成器
    :param window: QMainWindow对象,也可以是loadUi返回的对象
    :param interval: 监听渲染结果的间隔时间, 单位: ms
    :return: ipcMain -> 任务IPC对象; ipcRenderer -> 渲染IPC对象
    """
    if not isinstance(interval, int):
        raise OperationException("Please pass the int type as the interval parameter!")
    ipcMain = IPCMain(window, interval)
    ipcRenderer = IPCRenderer(ipcMain)
    ipcMain.bind_quit()
    ipcMain.run()

    return ipcMain, ipcRenderer
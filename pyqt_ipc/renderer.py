from PyQt5.QtWidgets import QApplication

from .logger import logger


__all__ = [
    "IPCRenderer"
]

class CallController:

    def __init__(self, callback):
        self._callbacks = [callback]

    def add(self, callback):
        """
        添加结果回调函数
        :param callback: 结果回调函数
        :return: None
        """
        self._callbacks.append(callback)

    def __call__(self, *args, **kwargs):
        """
        调用回调函数
        :param args:
        :param kwargs:
        :return:
        """
        for callback in self._callbacks:
            callback(*args, **kwargs)

        QApplication.processEvents()

class IPCRenderer:

    def __init__(self, ipcMain):

        self._ipcMain = ipcMain

    def on(self, task_name, callback):
        """
        添加任务监听
        :param task_name: 任务名称
        :param callback: 结果回调函数
        :return: None
        """
        if task_name in self._ipcMain.listen_always_tasks:
            self._ipcMain.listen_always_tasks[task_name].add(callback)
        else:
            new_always_tasks = self._ipcMain.listen_always_tasks
            new_always_tasks[task_name] = CallController(callback)
            self._ipcMain.listen_always_tasks = new_always_tasks
        logger.debug(f"任务名({task_name})成功添加渲染监听")

    def once(self, task_name, callback):
        """
        添加单次任务监听
        :param task_name: 任务名称
        :param callback: 结果回调函数
        :return: None
        """
        if task_name in self._ipcMain.listen_once_tasks:
            self._ipcMain.listen_once_tasks[task_name].add(callback)
        else:
            new_once_tasks = self._ipcMain.listen_once_tasks
            new_once_tasks[task_name] = CallController(callback)
            self._ipcMain.listen_once_tasks = new_once_tasks
        logger.debug(f"任务名({task_name})成功添加单次渲染监听")

    def cancel(self, task_name):
        """
        取消任务监听
        :param task_name: 任务名称
        :return: None
        """
        if task_name in self._ipcMain.listen_always_tasks:
            new_always_tasks = self._ipcMain.listen_always_tasks
            del new_always_tasks[task_name]
            self._ipcMain.listen_always_tasks = new_always_tasks

        if task_name in self._ipcMain.listen_once_tasks:
            new_once_tasks = self._ipcMain.listen_once_tasks
            del new_once_tasks[task_name]
            self._ipcMain.listen_once_tasks = new_once_tasks
        logger.debug(f"任务名({task_name})成功取消所有监听")
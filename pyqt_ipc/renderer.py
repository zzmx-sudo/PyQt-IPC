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
        添加回调函数
        :param callback: 结果回调函数
        :return: None
        """
        self._callbacks.append(callback)

    def remove(self, callback):
        """
        移除回调函数
        :return: bool
        """
        if callback not in self._callbacks:
            return False

        self._callbacks.remove(callback)
        return True

    def clear(self):
        """
        清空回调函数
        :return: None
        """
        self._callbacks.clear()

    def empty(self):

        return not self._callbacks

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
        添加任务回调
        :param task_name: 任务名称
        :param callback: 结果回调函数
        :return: None
        """
        if task_name in self._ipcMain.listen_tasks:
            self._ipcMain.listen_tasks[task_name].add(callback)
        else:
            new_listen_tasks = self._ipcMain.listen_tasks
            new_listen_tasks[task_name] = CallController(callback)
            self._ipcMain.listen_tasks = new_listen_tasks
        logger.debug(f"[{task_name}]: 添加任务监听成功")

    def remove(self, task_name, callback):
        """
        移除任务单个回调
        :param task_name: 任务名称
        :param callback: 回调函数
        :return: None
        """
        if task_name not in self._ipcMain.listen_tasks:
            logger.warning(f"[{task_name}]: 未添加任务监听, 请添加监听后再移除, 本次移除操作被忽略!")
            return

        if not self._ipcMain.listen_tasks[task_name].remove(callback):
            logger.warning(f"[{task_name}]: 该回调未被添加未监听, 请先添加为监听后再移除, 本次移除操作被忽略!")
            return

        if self._ipcMain.listen_tasks[task_name].empty():
            new_listen_tasks = self._ipcMain.listen_tasks
            del new_listen_tasks[task_name]
            self._ipcMain.listen_tasks = new_listen_tasks

        logger.debug(f"[{task_name}]: 移除任务单个监听成功")

    def cancel(self, task_name):
        """
        清空任务回调
        :param task_name: 任务名称
        :return: None
        """
        if task_name in self._ipcMain.listen_tasks:
            new_listen_tasks = self._ipcMain.listen_tasks
            del new_listen_tasks[task_name]
            self._ipcMain.listen_tasks = new_listen_tasks

        logger.debug(f"[{task_name}]: 清空任务监听成功")
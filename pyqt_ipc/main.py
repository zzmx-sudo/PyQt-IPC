import time
from multiprocessing import Process, Queue

import psutil
from PyQt5.QtCore import pyqtSignal, QThread

from .task import TaskManager
from .exception import ProcessException


__all__ = [
    "IPCMain"
]

task_q = Queue()
result_q = Queue()

class WatchThread(QThread):
    """
    Watch结果线程
    """
    signal = pyqtSignal(tuple)

    def __init__(self, run_flag=True):
        super(WatchThread, self).__init__()
        self._run_flag = run_flag

    def run(self):

        while True:
            if not self._run_flag:
                break

            if result_q.empty():
                time.sleep(0.2)
                continue

            result = result_q.get()
            self.signal.emit(result)

    @property
    def run_flag(self):

        return self._run_flag

    @run_flag.setter
    def run_flag(self, newValue):

        self._run_flag = newValue

class IPCMain:

    def __init__(self, window):

        self._window = window
        self._task_names = []
        self._proc = None
        self._watch_thread = None
        self._listen_always_tasks = {}
        self._listen_once_tasks = {}

    def registry(self, task_name, task):
        """
        注册/更新任务
        :param task_name: 任务名称
        :param task: 任务实体
        :return: None
        """
        if task_name in self._task_names:
            task_q.put(("modify", task_name, task))
        else:
            task_q.put(("add", task_name, task))
            self._task_names.append(task_name)

    def start(self, task_name, *args, **kwargs):
        """
        启动任务
        :param task_name: 任务名称
        :param args: 执行任务传递的位置参数
        :param kwargs: 执行任务传递的关键字参数
        :return: None
        """
        if task_name not in self._task_names:
            raise ProcessException("请先完成任务注册后再启动")

        task_q.put(("start", task_name, args, kwargs))

    def cancel(self, task_name):
        """
        停止任务
        :param task_name: 任务名称
        :return: None
        """
        if task_name not in self._task_names:
            raise ProcessException("任务完成注册并运行后才有停止的可能")

        task_q.put(("stop", task_name))

    def bind_quit(self):
        """
        给Qt退出增加IPC退出操作
        :return: None
        """
        closeEvent = self._window.closeEvent

        def _quit(event):
            if self._watch_thread is not None:
                self._watch_thread.run_flag = False
                self._watch_thread.quit()

            task_q.put(("stop-all",))
            self.__kill_proc()

            closeEvent(event)

        self._window.closeEvent = _quit

    def run(self):
        """
        任务管理进程启动
        :return: None
        """
        self._proc = Process(target=TaskManager.run_ever, args=(task_q, result_q))
        self._proc.daemon = True
        self._proc.start()

        self._watch_thread = WatchThread(True)
        self._watch_thread.signal.connect(self._callback)
        self._watch_thread.start()

    def _callback(self, result):
        """
        结果回调
        :param result: 任务完成后生成的结果
        :return: None
        """
        task_name = result[0]
        if task_name in self._listen_always_tasks:
            self._listen_always_tasks[task_name](*result[1:])

        if task_name in self._listen_once_tasks:
            self._listen_once_tasks[task_name](*result[1:])
            del self._listen_once_tasks[task_name]

    @property
    def listen_always_tasks(self):

        return self._listen_always_tasks

    @listen_always_tasks.setter
    def listen_always_tasks(self, newValue):

        self._listen_always_tasks = newValue

    @property
    def listen_once_tasks(self):

        return self._listen_once_tasks

    @listen_once_tasks.setter
    def listen_once_tasks(self, newValue):

        self._listen_once_tasks = newValue

    def __kill_proc(self):
        """
        任务管理进程关闭
        :return: None
        """
        if self._proc is None:
            return

        process = psutil.Process(self._proc.pid)
        for child in process.children(recursive=True):
            child.kill()

        process.kill()

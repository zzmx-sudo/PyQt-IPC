import time
import inspect
from multiprocessing import Process, Queue

import psutil
from PyQt5.QtCore import pyqtSignal, QThread

from .task import TaskManager, TaskIterator
from .logger import logger


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

    def __init__(self, interval, run_flag=True):
        super(WatchThread, self).__init__()
        self._interval = interval
        self._run_flag = run_flag

    def run(self):

        while True:
            if not self._run_flag:
                break

            if result_q.empty():
                time.sleep(self._interval)
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

    def __init__(self, window, interval):

        self._window = window
        self._interval = interval / 1000
        self._task_datasets = {}
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
        if task_name in self._task_datasets:
            ori_task_info = self._task_datasets[task_name]
            ori_task = ori_task_info["task"]
            already_cycle = ori_task_info["already"]
            if isinstance(ori_task, TaskIterator):
                if ori_task.cycles == 0 or already_cycle < ori_task.cycles:
                    logger.warning(f"任务名({task_name})对应的任务还在运行中, 任务完成后才能重新注册任务, 本次注册被忽略!")
                    return
            else:
                if already_cycle == 0:
                    logger.warning(f"任务名({task_name})对应的任务还在运行中, 任务完成后才能重新注册任务, 本次注册被忽略!")
                    return
            task_q.put(("modify", task_name, task))
        else:
            task_q.put(("add", task_name, task))

        self._task_datasets.update({task_name: {"task": task, "already": 0}})
        logger.debug(f"任务名({task_name})下发注册/更新成功")

    def start(self, task_name, *args, **kwargs):
        """
        启动任务
        :param task_name: 任务名称
        :param args: 执行任务传递的位置参数
        :param kwargs: 执行任务传递的关键字参数
        :return: None
        """
        if task_name not in self._task_datasets:
            logger.error("流程错误, 请先完成任务注册后再启动, 本次启动被忽略!")
            return

        if not self._validate_task_params(task_name, *args, **kwargs):
            logger.error("操作错误, 传递给任务的参数不合法, 请传递有效参数, 本次启动被忽略!")
            return

        task_q.put(("start", task_name, args, kwargs))
        logger.debug(f"任务名({task_name})下发启动成功")

    def cancel(self, task_name):
        """
        停止任务
        :param task_name: 任务名称
        :return: None
        """
        if task_name not in self._task_datasets:
            logger.error("流程错误, 任务完成注册并运行后才有停止的可能, 本次停止任务操作被忽略!")
            return

        if task_name in self._listen_always_tasks:
            del self._listen_always_tasks[task_name]

        if task_name in self._listen_once_tasks:
            del self._listen_once_tasks[task_name]
        logger.debug(f"任务名({task_name})已成功取消所有渲染监听")

        task_q.put(("stop", task_name))
        logger.debug(f"任务名({task_name})下发取消成功")

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

        if task_name in self._task_datasets:
            self._callback_logging(task_name)

    def _validate_task_params(self, task_name, *args, **kwargs):
        """
        校验传递给任务参数是否合法
        :param task_name: 任务名称
        :param args: 传递给任务的位置参数
        :param kwargs: 传递给任务的关键字参数
        :return: bool -> 是否校验成功
        """
        task = self._task_datasets[task_name]["task"]
        if isinstance(task, TaskIterator):
            task = task.taskProto
        sig = inspect.signature(task)
        params = sig.parameters
        if len(args) > len(params):
            return False

        kwargs_keys = [x for x in params][len(args):]
        for kwargs_key in kwargs_keys:
            if params[kwargs_key].default is inspect._empty and kwargs_key not in kwargs:
                return False

        return True

    def _callback_logging(self, task_name):
        """
        任务回调后写日志操作
        :param task_name: 任务名称
        :return: None
        """
        task_info = self._task_datasets[task_name]
        task_obj = task_info["task"]
        already_cycle = task_info["already"]
        already_cycle += 1
        task_info.update({"already": already_cycle})
        if isinstance(task_obj, TaskIterator):
            if task_obj.cycles == 0 or already_cycle < task_obj.cycles:
                logger.debug(f"任务名({task_name})第 {already_cycle} 次任务结束")
            else:
                logger.info(f"任务名({task_name})对应任务已全部结束")
        else:
            logger.info(f"任务名({task_name})已经结束")

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

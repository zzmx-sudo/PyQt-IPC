import time
from threading import Thread

from .exception import RegistryException, OperationException


__all__ = [
    "TaskIterator",
    "TaskManager"
]

class TaskIterator:

    def __init__(self, task, cycles=0):
        self.__tasks = task
        self._cycles = cycles
        self.__cycle = 0

    def __iter__(self):

        return self

    def __next__(self):

        if self.__cycle < self._cycles or self._cycles == 0:
            self.__cycle += 1
            return self.__tasks
        else:
            raise StopIteration

    def reload(self):
        """
        重置任务
        :return: None
        """
        self.__cycle = 0

    @property
    def taskProto(self):

        return self.__tasks

    @taskProto.setter
    def taskProto(self, newValue):

        raise OperationException("不支持通过该方式修改任务本体")

class Task:

    def __init__(self, task_name, task, result_q):
        if isinstance(task, TaskIterator):
            self._task = task
        elif hasattr(task, "__call__"):
            self._task = TaskIterator(task, cycles=1)
        else:
            raise RegistryException("任务必须为可调用的,它可以是一个函数或TaskIterator实例对象")

        self._run = False
        self._task_name = task_name
        self._result_q = result_q

    def run(self, *args, **kwargs):
        """
        启动任务
        :return: None
        """
        self._run = True
        for task in self._task:
            if not self._run:
                return

            result = task(*args, **kwargs)
            if isinstance(result, tuple):
                self._result_q.put((self._task_name, *result))
            else:
                self._result_q.put((self._task_name, result))

        self._run = False

    def quit(self):
        self._run = False

    def reload(self):
        """
        重置任务
        :return: None
        """
        self._task.reload()

    @property
    def isRuning(self):

        return self._run

    @property
    def task(self):

        return self._task

    @task.setter
    def task(self, newValue):

        if self.isRuning:
            raise OperationException("任务正在运行中，不允许重新注册")

        if isinstance(newValue, TaskIterator):
            self._task = newValue
        elif hasattr(newValue, "__call__"):
            self._task = TaskIterator(newValue, cycles=1)
        else:
            raise RegistryException("任务必须为可调用的,它可以是一个函数或TaskIterator实例对象")

class TaskManager:

    def __init__(self, result_q):

        self._result_q = result_q
        self._all_tasks = {}

    @classmethod
    def run_ever(cls, task_q, result_q):
        """
        接收任务并执行
        :param task_q: 任务队列
        :param output_q: 结果队列
        :return: None
        """
        manager = cls(result_q)

        while True:
            task_params = task_q.get()
            task_type = task_params[0]
            if task_type == "add":
                manager._add_task(*task_params[1:])
            elif task_type == "modify":
                manager._modify_task(*task_params[1:])
            elif task_type == "start":
                manager._start_task(*task_params[1:])
            elif task_type == "stop":
                manager._stop_task(*task_params[1:])
            elif task_type == "stop-all":
                manager._stop_all()

    def _add_task(self, task_name, task):
        """
        添加/注册任务
        :param task_name: 任务名称
        :param task: 任务实体
        :return: None
        """
        self._all_tasks[task_name] = Task(task_name, task, self._result_q)

    def _modify_task(self, task_name, task):
        """
        修改任务
        :param task_name: 任务名称
        :param task: 任务实体
        :return: None
        """
        self._all_tasks[task_name].task = task

    def _start_task(self, task_name, args, kwargs):
        """
        开启任务
        :param task_name: 任务名称
        :param args: 执行任务的位置参数
        :param kwargs: 执行任务的关键字参数
        :return: None
        """
        if self._all_tasks[task_name].isRuning:
            return

        self._all_tasks[task_name].reload()
        t = Thread(target=self._all_tasks[task_name].run, args=args, kwargs=kwargs)
        t.setDaemon(True)
        t.start()

    def _stop_task(self, task_name):
        """
        停止任务
        :param task_name: 任务名称
        :return: None
        """
        self._all_tasks[task_name].quit()

    def _stop_all(self):
        """
        停止所有任务
        :return: None
        """
        for task in self._all_tasks.values():
            task.quit()
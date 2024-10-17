## 版本
v0.2.0

## 背景
PyQt在进行任何耗时操作时将堵塞Qt的渲染导致Qt界面卡顿，Qt程序免不了耗时操作，故设计此工具用简单的操作注册运行耗时任务，并完成任务和渲染的通信/交互。

## 说明
本repo用于PyQt耗时任务执行/操作
- By: 大宝天天见丶(zzmx-sudo)

基于PyQt5开发

所用技术栈：

- PyQt5

依赖:

- PyQt5
- psutil

## 快速入门
```python
import sys
import os
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QTextEdit
from pyqt_ipc import CreateIPC

# 首先有个简单的Qt案例
class Example(QMainWindow):

    def __init__(self):
        super(Example, self).__init__()

        self.initUi()

    def initUi(self):
        # 创建任务ipc和渲染ipc对象
        self.ipcMain, self.ipcReanderer = CreateIPC(self)

        self.setWindowTitle("PyQt-IPC Demo")
        self.resize(400, 400)
        self.btn = QPushButton("点我展示文本内容", self)
        self.btn.resize(self.btn.sizeHint())
        self.btn.move(10, 10)
        # 控件绑定 启动任务事件
        self.btn.clicked.connect(lambda :self._start_read_file_once())
        
        self.btn2 = QPushButton("取消文本展示", self)
        self.btn2.resize(self.btn.sizeHint())
        self.btn2.move(120, 10)
        # 控件绑定 取消任务事件
        self.btn2.clicked.connect(lambda: self._cancel_read_file_once())
        self.textBox = QTextEdit(self)
        self.textBox.resize(380, 350)
        self.textBox.move(10, 40)
        
        # 控件初始化完成后, 窗口show之前开始初始化异步任务并添加监听
        self._init_async_tasks_and_listen()
        
        self.show()
    
    def _init_async_tasks_and_listen(self):
        """
        初始化异步任务并添加监听
        :return: None
        """
        # 注册任务
        self.ipcMain.registry("read_file_once", self._read_file)
        # 添加任务监听, 支持单任务监听多次(多个回调), 多次调用即可
        self.ipcReanderer.on("read_file_once", self.textBox.setText)
    
    def _start_read_file_once(self):
        """开启异步任务, 并携带任务参数"""
        self.ipcMain.start("read_file_once", "./demo.txt")
    
    def _cancel_read_file_once(self):
        """取消任务, 注意: 监听不会去除"""
        self.ipcMain.cancel("read_file_once")
    
    def _remove_listen(self):
        """移除任务的单个监听"""
        self.ipcReanderer.remove("read_file_once", self.textBox.setText)
    
    def _cancel_listen(self):
        """清空任务的所有监听"""
        self.ipcReanderer.cancel("read_file_once")

    @staticmethod
    def _read_file(file_path):
        """定义任务函数"""
        if not os.path.exists(file_path):
            return ""

        with open(file_path, "r") as f:
            return f.read()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Example()
    sys.exit(app.exec_())
```

#### 还可以是无限循环进行下去的任务
```python
# 先导入任务迭代器，迭代器默认任务无限循环运行
from pyqt_ipc.task import TaskIterator

# 将你的任务用TaskIterator包一层即可,若是有限次数任务,请传入cycles数
# 需要注意任务返回结果频率,若是瞬时(就像示例中那样)且频繁的任务,请适当添加阻塞,否则Qt将因吃不消导致崩溃
self.ipcMain.registry("read_file_forever", TaskIterator(self._read_file))

# 当你想关闭无限任务时，调用一次cancel即可
self.ipcMain.cancel("read_file_forever")
```

## 使用注意:
- 取消任务不会取消对应监听, 若不再监听请通过渲染ipc的remove/cancel方法移除监听
- 取消任务时若为循环任务, 后续的执行会被取消, 但当前被拉起的执行不会取消 且若存在监听会执行, 若无需监听请通过渲染ipc的remove/cancel方法移除监听
- 日志等级默认为`DEBUG`, 若要调节或关闭日志请至`logger.py`中配置
## 版本
v0.1.1

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
        # 控件绑定 注册/监听/启动任务事件
        self.btn.clicked.connect(lambda :self._read_file_once())
        
        self.btn2 = QPushButton("取消文本展示", self)
        self.btn2.resize(self.btn.sizeHint())
        self.btn2.move(120, 10)
        # 控件绑定 取消任务事件
        self.btn2.clicked.connect(lambda: self.ipcMain.cancel("read_file_once"))
        self.textBox = QTextEdit(self)
        self.textBox.resize(380, 350)
        self.textBox.move(10, 40)

        self.show()
    
    def _read_file_once(self):
        # 注册任务
        self.ipcMain.registry("read_file_once", self._read_file)
        # 定义监听任务结果回调,允许单任务多个监听,多次调用即可
        self.ipcReanderer.once("read_file_once", self.textBox.setText)
        # 单次监听任务结果回调,同样允许单任务多个监听
        self.ipcMain.start("read_file_once", "./pyqt_ipc/demo.txt")

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
# 同时, 任务监听改为on方法监听(once监听仅会回调一次, 后续任务的结果将会丢弃)
self.ipcReanderer.on("read_file_forever", self.textBox.append)

# 当你想关闭无限任务时，调用一次cancel即可, 此时该任务的所有监听都会移除
self.ipcMain.cancel("read_file_forever")
```

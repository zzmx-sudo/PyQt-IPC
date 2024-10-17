import sys
import os
import time
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QTextEdit
from pyqt_ipc import CreateIPC
from pyqt_ipc.task import TaskIterator

class Example(QMainWindow):

    def __init__(self, forever = False):
        self._forever = forever
        super(Example, self).__init__()

        self.initUi()

    def initUi(self):
        self.ipcMain, self.ipcReanderer = CreateIPC(self)

        self.setWindowTitle("PyQt-IPC Demo (by: zzmx-sudo)")
        self.resize(400, 400)
        self.btn = QPushButton("点我展示文本内容", self)
        self.btn.resize(self.btn.sizeHint())
        self.btn.move(10, 10)
        if self._forever:
            self.btn.clicked.connect(lambda :self._start_read_file_forever())
        else:
            self.btn.clicked.connect(lambda :self._start_read_file_once())

        self.btn2 = QPushButton("取消文本展示", self)
        self.btn2.resize(self.btn.sizeHint())
        self.btn2.move(120, 10)
        if self._forever:
            self.btn2.clicked.connect(lambda: self.ipcMain.cancel("read_file_forever"))
        else:
            self.btn2.clicked.connect(lambda: self.ipcMain.cancel("read_file_once"))

        self.textBox = QTextEdit(self)
        self.textBox.resize(380, 350)
        self.textBox.move(10, 40)

        self._init_async_tasks_and_listen()

        self.show()

    def _init_async_tasks_and_listen(self):
        """
        初始化异步任务并添加监听
        :return: None
        """
        self.ipcMain.registry("read_file_forever", TaskIterator(self._read_file))
        self.ipcReanderer.on("read_file_forever", self.textBox.append)

        self.ipcMain.registry("read_file_once", self._read_file)
        self.ipcReanderer.on("read_file_once", self.textBox.setText)

    def _start_read_file_forever(self):
        self.ipcMain.start("read_file_forever", "./demo.txt")

    def _start_read_file_once(self):
        self.ipcMain.start("read_file_once", "./demo.txt")

    def _remove_listen(self):
        self.ipcReanderer.remove("read_file_forever", self.textBox.append)
        self.ipcReanderer.remove("read_file_once", self.textBox.setText)

    def _cancel_listen(self):
        self.ipcReanderer.cancel("read_file_forever")
        self.ipcReanderer.cancel("read_file_once")

    @staticmethod
    def _read_file(file_path):
        time.sleep(1)

        if not os.path.exists(file_path):
            return ""

        with open(file_path, "r") as f:
            return f.read()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Example(False)
    sys.exit(app.exec_())
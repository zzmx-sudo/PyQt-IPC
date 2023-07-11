import sys
import os
import time
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QTextEdit
from pyqt_ipc import CreateIPC
from pyqt_ipc.task import TaskIterator

class Example(QMainWindow):

    def __init__(self):
        super(Example, self).__init__()

        self.initUi()

    def initUi(self):
        self.ipcMain, self.ipcReanderer = CreateIPC(self)

        self.setWindowTitle("PyQt-IPC Demo (by: zzmx-sudo)")
        self.resize(400, 400)
        self.btn = QPushButton("点我展示文本内容", self)
        self.btn.resize(self.btn.sizeHint())
        self.btn.move(10, 10)
        self.btn.clicked.connect(lambda :self.ipcMain.start("read_file", "./pyqt_ipc/demo_aaa.txt"))

        self.btn2 = QPushButton("取消文本展示", self)
        self.btn2.resize(self.btn.sizeHint())
        self.btn2.move(120, 10)
        self.btn2.clicked.connect(lambda: self.ipcMain.cancel("read_file"))

        self.textBox = QTextEdit(self)
        self.textBox.resize(380, 350)
        self.textBox.move(10, 40)

        self._setting_async_tasks()

        self.show()

    def _setting_async_tasks(self):
        self.ipcMain.registry("read_file", TaskIterator(self._read_file))
        self.ipcReanderer.on("read_file", self.textBox.append)
        # self.ipcReanderer.once("read_file", self.textBox.setText)

    @staticmethod
    def _read_file(file_path):
        time.sleep(1)

        if not os.path.exists(file_path):
            return ""

        with open(file_path, "r") as f:
            return f.read()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Example()
    sys.exit(app.exec_())
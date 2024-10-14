import logging
from typing import Optional


class Logger:

    def __init__(self, level):
        self._level = level
        self._logger: Optional[logging.Logger] = None
        self._setup()

    def _setup(self):
        self._logger = logging.getLogger("pyqt-ipc")
        self._logger.setLevel(self._level)

        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)

        formatter = logging.Formatter("[%(asctime)s] [%(filename)s:%(lineno)d] [%(levelname)s]- %(message)s")
        console.setFormatter(formatter)

        self._logger.addHandler(console)
        self._logger.propagate = False

    @property
    def proto(self):

        return self._logger


logger = Logger(logging.INFO).proto
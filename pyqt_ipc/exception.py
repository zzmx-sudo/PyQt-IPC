__all__ = [
    "RegistryException",
    "ProcessException",
    "OperationException"
]

class IPCException(Exception):

    def __init__(self, msg):

        self._msg = msg

    def __str__(self):

        return self._msg

class RegistryException(IPCException):

    def __init__(self, msg):

        self._msg = f"注册失败，{msg}!"

class ProcessException(IPCException):

    def __init__(self, msg):

        self._msg = f"流程错误，{msg}"

class OperationException(IPCException):

    def __init__(self, msg):

        self._msg = f"操作错误，{msg}"
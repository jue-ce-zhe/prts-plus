class ErrorToLog(Exception):
    def __init__(self, message: str, isError: bool = True):
        self.message = f"错误：{message}" if isError else f"{message}"
    pass
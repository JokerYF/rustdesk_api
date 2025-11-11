class BaseError(Exception):
    """
    自定义异常基类
    """

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class UserNotFoundError(BaseError):
    """
    用户不存在
    """

    def __init__(self, username):
        super().__init__(f"用户不存在: {username}")

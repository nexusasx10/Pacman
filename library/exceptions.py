

class GameError(Exception):
    pass


class ResourceLoadingError(GameError):
    def __init__(self, critical, *args, **kwargs):
        super().__init__()
        self.critical = critical
        self.message = kwargs.get('message')

    def __str__(self):
        return f'{ResourceLoadingError}({self.message})'

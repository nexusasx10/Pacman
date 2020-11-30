

class GameError(Exception):
    pass


class ResourceLoadingError(GameError):
    def __init__(self, critical, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.critical = critical

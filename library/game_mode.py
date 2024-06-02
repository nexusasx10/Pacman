class GameMode:

    def __init__(self):
        self.rules = []

    def activate(self):
        for rule in self.rules:
            rule.activate(self)


class GameRule:

    def __init__(self):
        self.game_mode = None

    def activate(self, game_mode):
        self.game_mode = game_mode

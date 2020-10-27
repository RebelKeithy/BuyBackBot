from datetime import datetime


class Contract:
    def __init__(self, player, items):
        self.player = player
        self.sent = str(datetime.now())
        self.items = items

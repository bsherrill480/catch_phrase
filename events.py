from shared_events import *


class BeginTurnEvent(CopyableEvent):
    def __init__(self, player, time_left, word):
        self.name = "Begin Turn Event"
        self.player = player
        self.time_left = time_left
        self.word = word
pb.setUnjellyableForClass(BeginTurnEvent, BeginTurnEvent)

class EndTurnEvent(CopyableEvent):
    def __init__(self, player, time_left):
        self.name = "Begin Turn Event"
        self.player = player
        self.time_left = time_left
pb.setUnjellyableForClass(EndTurnEvent, EndTurnEvent)

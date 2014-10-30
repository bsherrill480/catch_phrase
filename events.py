from shared_events import *


class BeginTurnEvent(CopyableEvent):
    def __init__(self, player, time_left, word):
        CopyableEvent.__init__(self)
        self.name = "Begin Turn Event"
        self.player = player
        self.time_left = time_left
        self.word = word
pb.setUnjellyableForClass(BeginTurnEvent, BeginTurnEvent)

class EndTurnEvent(CopyableEvent):
    def __init__(self, player, time_left):
        CopyableEvent.__init__(self)
        self.name = "End Turn Event"
        self.player = player
        self.time_left = time_left
pb.setUnjellyableForClass(EndTurnEvent, EndTurnEvent)

class EndRoundEvent(CopyableEvent):
    def __init__(self):
        CopyableEvent.__init__(self)
        self.name = "End Round Event"
pb.setUnjellyableForClass(EndRoundEvent, EndRoundEvent)

class StartRoundEvent(CopyableEvent):
    def __init__(self):
        CopyableEvent.__init__(self)
        self.name = "Start Round Event"
pb.setUnjellyableForClass(StartRoundEvent, StartRoundEvent)


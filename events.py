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

class ToHandoffToEvent(CopyableEvent):
    def __init__(self, my_id, to_handoff_to):
        """
        to_handoff_to is client_id
        """
        CopyableEvent.__init__(self)
        self.my_id = my_id
        self.name = "To Handoff To Event"
        self.to_handoff_to = to_handoff_to
pb.setUnjellyableForClass(ToHandoffToEvent, ToHandoffToEvent)

class NewPlayerEvent(CopyableEvent):
    def __init__(self, client_id, nickname):
        CopyableEvent.__init__(self)
        self.client_id = client_id
        self.nickname = nickname
pb.setUnjellyableForClass(NewPlayerEvent, NewPlayerEvent)
class NewOrderingEvent(CopyableEvent):
    def __init__(self, in_order, waiting):
        CopyableEvent.__init__(self)
        self.name = "New Order Event"
        self.in_order = in_order
        self.waiting = waiting
pb.setUnjellyableForClass(NewOrderingEvent, NewOrderingEvent)
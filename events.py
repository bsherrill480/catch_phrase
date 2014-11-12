from shared_events import *


class BeginTurnEvent(CopyableEvent):
    def __init__(self, client_id, nickname, time_left, word):
        CopyableEvent.__init__(self)
        self.name = "Begin Turn Event"
        self.nickname = nickname
        self.client_id = client_id
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
    def __init__(self, scores):
        CopyableEvent.__init__(self)
        self.name = "End Round Event"
        self.scores = scores
pb.setUnjellyableForClass(EndRoundEvent, EndRoundEvent)


class StartRoundEvent(CopyableEvent):
    def __init__(self):
        CopyableEvent.__init__(self)
        self.name = "Start Round Event"
pb.setUnjellyableForClass(StartRoundEvent, StartRoundEvent)

class WrongOrderingEvent(CopyableEvent):
    def __init__(self, print_out_list):
        CopyableEvent.__init__(self)
        self.name = "Wrong Ordering Event"
        self.print_out_list = print_out_list
pb.setUnjellyableForClass(WrongOrderingEvent, WrongOrderingEvent)


class GameStartEvent(CopyableEvent):
    def __init__(self):
        CopyableEvent.__init__(self)
        self.name = "Game Start Event"
pb.setUnjellyableForClass(GameStartEvent, GameStartEvent)


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


class NewPlayerLineupEvent(CopyableEvent):
    def __init__(self, id_nickname_list, waiting_list):
        """
        id_nickname list is setup like [ (player.id, player.nickname) for each player ]
        """
        CopyableEvent.__init__(self)
        self.name = "New Player Lineup Event"
        self.id_nickname_list = id_nickname_list
        self.waiting_list = waiting_list
pb.setUnjellyableForClass(NewPlayerLineupEvent, NewPlayerLineupEvent)

class EndGameEvent(CopyableEvent):
    def __init__(self):
        CopyableEvent.__init__(self)
pb.setUnjellyableForClass(EndGameEvent, EndGameEvent)


class StartGameRequestEvent(CopyableEvent):
    def __init__(self):
        CopyableEvent.__init__(self)
        self.name = "Start Game Requst Event"
pb.setUnjellyableForClass(StartGameRequestEvent, StartGameRequestEvent)

# class NewWaitingEvent(CopyableEvent):
#     def __init__(self, waiting_list):
#         CopyableEvent.__init__(self)
#         self.waiting_list = waiting_list
# pb.setUnjellyableForClass(NewWaitingEvent, NewWaitingEvent)

# class NewOrderingEvent(CopyableEvent):
#     def __init__(self, in_order, waiting):
#         CopyableEvent.__init__(self)
#         self.name = "New Order Event"
#         self.in_order = in_order
#         self.waiting = waiting
# pb.setUnjellyableForClass(NewOrderingEvent, NewOrderingEvent)
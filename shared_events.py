from twisted.spread import pb
#Events that are local to server
class Event(object):
    def __init__(self):
        self.name = "Generic Event"
        self.originator = None
        self.pass_through = True #i.e. goes through gamestack to game

class TickEvent(Event):
    def __init__(self):
        Event.__init__(self)
        self.name = "Tick Event"


#Events which need to be sent through network
class CopyableEvent(pb.RemoteCopy, pb.Copyable, Event):
    def __init__(self):
        super(CopyableEvent, self).__init__()
        self.name = "Generic Event"

class PlayerJoinedEvent(CopyableEvent):
    def __init__(self, player):
        CopyableEvent.__init__(self)
        self.name = "Player Joined Event"
        self.player = player
pb.setUnjellyableForClass(PlayerJoinedEvent, PlayerJoinedEvent)


from model import Model
from game_stack import GameStack
from twisted.spread import pb
from twisted.internet import reactor #This isn't used, but maybe Looping cal needs?
from twisted.internet.task import LoopingCall #Nope this is used...
from collections import deque
import events as e


class GameEventManager():
    """
    handles game events. game does not care about client's notify
    """
    def __init__(self, clients, game_over_callback, player_observers):
        #externally stuff refers to done in setup_catch_phrase
        self.clients = clients #list of clients
        for client in self.clients:
            client.observers.append(self)
        self.game_over_callback = game_over_callback
        self.game_stack = None # needs to be set externally
        self.model = None # needs to be set externally
        #self.looping_call_clients = None #check for dead clients.
        self.looping_call_self = LoopingCall(self.post, e.TickEvent()) #give myself TickEvents
                                                             #needs to be started externally
        self.event_queue = deque()# O(1) leftpop()
        self.__in_loop = False
        self.player_observers = player_observers
        self.lobby_id = None #REMOVE WHEN DONE DEBUGGING
    def dead_client(self, client):
        self.post(e.CopyableEvent()) #post takes care of dead clients

    def post(self, event):
        """
        posts to clients. Handles if they leave.
        """
        #TODO: see why I did this. Was I just tired or was there a reason?
        # if not self.looping_call_clients: #setup because we can't in __init__?
        #     self.looping_call_clients = LoopingCall(self.post, e.CopyableEvent())#check for pulse of clients
        #     self.looping_call_clients.start(15.0) #every 15 seconds
        event.lobby_id = self.lobby_id
        is_tick_event = isinstance(event, e.TickEvent)
        if (not self.__in_loop) and is_tick_event:
            self.__in_loop = True
            while len(self.event_queue) > 0:
                event = self.event_queue.popleft()
                self._single_event_notify(event)
                if self.clients == []: #if game is over (clients are all gone)
                    self.game_over_callback()
                    self.looping_call_self.stop()
                    break
            self.event_queue.clear()
            self.__in_loop = False

        elif not is_tick_event:
            self.event_queue.append(event)

    def _single_event_notify(self, event):
        """
        Notifies clients of a single event. Removes clients if they are dead
        and updates game appropriately.
        """
        clients_to_remove = []
        if not isinstance(event, e.TickEvent): #I shouldn't be seeing any tick events, can remove later
            for client in self.clients:
                try:
                    client.root_obj.callRemote("notify", event)
                except pb.DeadReferenceError:
                    clients_to_remove.append(client)
        if isinstance(event, e.QuitEvent):
            print event.client_id, " is quitting"
            #fuck effeciency, get readability!
            for client in self.clients:
                if client.client_id == event.client_id and client not in clients_to_remove:
                    clients_to_remove.append(client)
        self.game_stack.notify(event) #let it generate begin event (if it was going to)
        for client in clients_to_remove:
            print "removing", client.client_id, client.nickname
            self.clients.remove(client)
            print "before self.model.players_order", self.model.players_order._order
            self.model.players_order.remove_all_item(client.client_id)
            print "after self.model.players_order", self.model.players_order._order

            ev = e.EndTurnEvent(client.client_id, self.model.time_left)
            ev.penis = True
            self.post(ev)
        self.obs_notify(event)

    def obs_notify(self, event):
        dead_clients = []
        for client in self.player_observers:
            try:
                client.root_obj.callRemote('notify', event)
            except pb.DeadReferenceError:
                dead_clients.append(client)
        for client in dead_clients:
            self.player_observers.remove(client)

class BaseGame:
    """
    Used by game_stack. Base game.
    model passed is "base model" in game_stack
    and a Model() object
    """
    def __init__(self, game_stack, model):
        self.game_stack = game_stack
        self.model = model
        self.round_time = model.round_time
        self.leeway_time = model.leeway_time
    def __call__(self, event):
        if isinstance(event, e.StartRoundEvent):
            self.game_stack.push(PlayerGuessGame(self.game_stack, self.round_time, self.leeway_time))


class PlayerGuessGame:
    """
    Used by game_stack. 2nd level game.
    """
    def __init__(self, game_stack, round_time, leeway_time):
        self.game_stack = game_stack
        self.round_time = round_time
        self.leeway_time = leeway_time
    def on_push(self):
        self.model = self.game_stack.get_model("base game")
        current_player = self.model.players_order.get_next()
        current_word = self.model.word_order.get_next()
        time_left = self.model.time_left
        begin_turn_event = e.BeginTurnEvent(current_player,
                    self.model.nicknames[current_player], time_left, current_word)
        self.game_stack.post(begin_turn_event)

    def __call__(self, event):
        if isinstance(event, e.EndTurnEvent) and self.model.players_order.current_item == event.player:
            if event.time_left <= 0.0:
                self.model.scores[event.player][0] -= 1 # scores is {client_id: [score, nickname]}
                self.model.time_left = self.round_time
                self.game_stack.post(e.EndRoundEvent(str(self.model.scores.values())))
            else:
                time_left = event.time_left
                if time_left < self.leeway_time and time_left > 0:
                    time_left = self.leeway_time
                self.model.time_left = time_left
                next_player = self.model.players_order.get_next()
                word = self.model.word_order.get_next()
                new_turn_event = e.BeginTurnEvent(next_player,
                                self.model.nicknames[next_player], time_left, word)
                self.game_stack.post(new_turn_event)
        elif isinstance(event, e.SkipWordEvent):
                word = self.model.word_order.get_next()
                player = self.model.players_order.current_item
                new_turn_event = e.BeginTurnEvent(player,
                                self.model.nicknames[player], event.time_left, word)
                self.game_stack.post(new_turn_event)
        elif isinstance(event, e.EndRoundEvent):
            self.game_stack.pop()


def setup_catch_phrase(players, word_list, player_order, game_over_callback,
                       round_time, leeway_time, player_observers, lobby_id = None):
    """
    returns event_manager for game
    players is a list of client objects (as defined in server)
    word list is just a list of words
    player_order is how turn should progress.
        should be list of client_id. Will be turned into circular list
    """
    event_manager = GameEventManager(players, game_over_callback, player_observers)
    game_stack = GameStack(event_manager)
    event_manager.game_stack = game_stack
    model = Model(player_order, word_list,
                  {player.client_id: player.nickname for player in players}, round_time, leeway_time)
    base_game = BaseGame(game_stack, model)
    event_manager.model = model
    game_stack.push(base_game, model, "base game")
    event_manager.looping_call_self.start(.25) # to check for dead clients
    event_manager.lobby_id = lobby_id #REMOVE WHEN DONE DEBUGGING
    return event_manager

if __name__ == '__main__':
    #for testing
    from twisted.internet import reactor
    from twisted.internet.task import LoopingCall
    from time import sleep
    from random import randint
    class client:
        class RootObj:
            def callRemote(self,crap,event):
                print event.name
                if isinstance(event, e.BeginTurnEvent):
                    sleep(.5)
                    print "   Player: ", event.player, " /// word: ", event.word
                    time_used = float(randint(3,8))
                    print "   I had: ", event.time_left, "s. After going I have: ", str(event.time_left - time_used)
                    fun = evm.post
                    value = e.EndTurnEvent(event.player, event.time_left - time_used)
                    reactor.callLater(1.5, fun, value)
                    #evm.remote_post(e.EndTurnEvent(event.player, event.time_left - 1.0))
        def __init__(self):
            self.root_obj = self.RootObj()
    evm = setup_catch_phrase({"client":client()},
                             ["cat", "dog", "back", "in","town","didn't","care how"], ['client1', 'client2'])
    evm.post(e.StartRoundEvent())
    looping_call = LoopingCall(evm.post, e.TickEvent())
    looping_call.start(2.0)
    reactor.run()


from model import Model
from game_stack import GameStack
from twisted.spread import pb
from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from collections import deque
import events as e


class GameEventManager():
    def __init__(self, clients, game_over_callback):
        self.clients = clients
        self.game_over_callback = game_over_callback
        self.game_stack = None # needs to be set
        self.model = None # needs to be set
        self.looping_call_clients = None
        self.looping_call_self = LoopingCall(self.post, e.TickEvent())
        self.event_queue = deque()
        self.__in_loop = False

    def post(self, event):
        if not self.looping_call_clients: #setup client cleanup
            self.looping_call_clients = LoopingCall(self.post, e.CopyableEvent())#check for pulse of clients
            self.looping_call_clients.start(15.0) #every 15 seconds
        is_tick_event = isinstance(event, e.TickEvent)
        if (not self.__in_loop) and is_tick_event:
            self.__in_loop = True
            while len(self.event_queue) > 0:
                event = self.event_queue.popleft()
                is_game_over = self._single_event_notify(event)
                if is_game_over:
                    break
            self.event_queue.clear()
            self.__in_loop = False
        elif not is_tick_event:
            self.event_queue.append(event)

    def _single_event_notify(self, event):
        """
        returns False if game is over, True otherwise
        """
        is_game_over = False
        clients_to_remove = []
        if not isinstance(event, e.TickEvent):
            for client in self.clients:
                try:
                    client.root_obj.callRemote("notify", event)
                except pb.DeadReferenceError:
                    # if isinstance(event, e.BeginTurnEvent) and client.client_id == event.client_id:
                    #     end_of_turn_event = e.EndTurnEvent(client.client_id,event.time_left)
                    #     end_of_turn_event.name = end_of_turn_event.name + " DEAD CLIENT, saw begin turn"
                    #     event_to_launch = end_of_turn_event
                    # else: #incase it was the clients turn when they left.
                    #     end_of_turn_event = e.EndTurnEvent(client.client_id, 30)
                    #     end_of_turn_event.name = end_of_turn_event.name + " DEAD CLIENT, No begin turn"
                    #     event_to_launch = end_of_turn_event
                    clients_to_remove.append(client)

        if isinstance(event, e.QuitEvent):
            for client in self.clients:
                if client.client_id == event.client_id and client not in clients_to_remove: #fuck effeciency!
                    clients_to_remove.append(client)
        self.game_stack.notify(event) #let it generate begin event
        for client in clients_to_remove:
            print "removing client:", client.client_id, client.nickname
            self.clients.remove(client)
            self.model.players_order.remove_player(client.client_id)
            self.post(e.EndTurnEvent(client.client_id,30))
        if self.clients == []:
            self.game_over_callback()
            self.looping_call_clients.stop()
            self.looping_call_self.stop()
            print "GAME OVER"
            is_game_over = True
        return is_game_over



class Game:
    def __init__(self, game_stack):
        self.game_stack = game_stack

class BaseGame:
    def __init__(self, game_stack, model):
        self.game_stack = game_stack
        self.model = model
    def __call__(self, event):
        if isinstance(event, e.StartRoundEvent):
            self.game_stack.push(PlayerGuessGame(self.game_stack))

class PlayerGuessGame(Game):
    def on_push(self):
        self.model = self.game_stack.get_model("base game")
        current_player = self.model.players_order.get_next()
        current_word = self.model.word_order.get_next()
        time_left = self.model.time_left
        begin_turn_event = e.BeginTurnEvent(current_player,
                    self.model.nicknames[current_player], time_left, current_word)
        self.game_stack.post(begin_turn_event)
    def __call__(self, event):
        if isinstance(event, e.EndTurnEvent):
        #     print event.player, event.time_left, event.name
        #     print "isinstance(event, e.EndTurnEvent) and self.model.players_order.current_player == event.player",
        #     isinstance(event, e.EndTurnEvent) and self.model.players_order.current_player == event.player
            print event, "current player",self.model.players_order.current_player, "event player", event.player

        if isinstance(event, e.EndTurnEvent) and self.model.players_order.current_player == event.player:
            if event.time_left <= 0.0:
                player_score = self.model.scores[event.player]
                print "*****ROUND OVER*****"
                self.model.scores[event.player] = player_score - 1
                print self.model.scores
                self.game_stack.post(e.EndRoundEvent(str(self.model.scores)))
            else:
                time_left = event.time_left
                if time_left < 5.0:
                    time_left = 5.0
                next_player = self.model.players_order.get_next()
                word = self.model.word_order.get_next()
                new_turn_event = e.BeginTurnEvent(next_player,
                                self.model.nicknames[next_player], time_left,word)
                self.game_stack.post(new_turn_event)
        elif isinstance(event, e.EndRoundEvent):
            self.game_stack.pop()


def setup_catch_phrase(players, word_list, player_order, game_over_callback):
    """
    returns event_manager for game

    players is a dictionary (client id: root_obj)
    word list is just a list of words
    player_order is how turn should progress
    """
    event_manager = GameEventManager(players, game_over_callback)
    game_stack = GameStack(event_manager)
    event_manager.game_stack = game_stack
    model = Model(player_order, word_list,
                  {player.client_id: player.nickname for player in players})
    base_game = BaseGame(game_stack, model)
    event_manager.model = model
    game_stack.push(base_game, model, "base game")
    event_manager.looping_call_self.start(.25)
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


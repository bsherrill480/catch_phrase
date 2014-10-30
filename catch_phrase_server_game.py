from model import Model
from game_stack import GameStack
from twisted.spread import pb
#for testing
from twisted.internet import reactor
from twisted.internet.task import LoopingCall
import events as e

class GameEventManager(pb.Root):
    def __init__(self, clients):
        self.clients = clients
        self.game_stack = None # needs to be set
    def remote_post(self, event):
        for client in self.clients.values():
            client.callRemote("notify", event)
        self.game_stack.notify(event)

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
        begin_turn_event = e.BeginTurnEvent(current_player, time_left, current_word)
        self.game_stack.post(begin_turn_event)
    def __call__(self, event):
        if isinstance(event, e.EndTurnEvent):
            if event.time_left <= 0.0:
                player_score = self.model.scores[event.player]
                print "*****ROUND OVER*****"
                self.model.scores[event.player] = player_score - 1
                print self.model.scores
                self.game_stack.post(e.EndRoundEvent())
            else:
                time_left = event.time_left
                if time_left < 5.0:
                    time_left = 5.0
                next_player = self.model.players_order.get_next()
                word = self.model.word_order.get_next()
                new_turn_event = e.BeginTurnEvent(next_player,time_left,word)
                self.game_stack.post(new_turn_event)
        elif isinstance(event, e.EndRoundEvent):
            self.game_stack.pop()


def setup_catch_phrase(players, word_list, player_order):
    """
    returns event_manager for game

    players is a dictionary (client id: root_obj)
    word list is just a list of words
    player_order is how turn should progress
    """
    event_manager = GameEventManager(players)
    game_stack = GameStack(event_manager)
    event_manager.game_stack = game_stack
    model = Model(player_order, word_list)
    base_game = BaseGame(game_stack, model)
    game_stack.push(base_game, model, "base game")

    return event_manager

if __name__ == '__main__':
    from time import sleep
    from random import randint
    class client:
        def callRemote(self,crap,event):
            print event.name
            if isinstance(event, e.BeginTurnEvent):
                sleep(.5)
                print "   Player: ", event.player, " /// word: ", event.word
                time_used = float(randint(3,8))
                print "   I had: ", event.time_left, "s. After going I have: ", str(event.time_left - time_used)
                fun = evm.remote_post
                value = e.EndTurnEvent(event.player, event.time_left - time_used)
                reactor.callLater(1.5, fun, value)
                #evm.remote_post(e.EndTurnEvent(event.player, event.time_left - 1.0))
    evm = setup_catch_phrase({"client":client()}, [], [])
    evm.remote_post(e.StartRoundEvent())
    looping_call = LoopingCall(evm.remote_post, e.TickEvent())
    looping_call.start(2.0)
    reactor.run()


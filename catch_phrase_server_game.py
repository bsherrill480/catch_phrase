from model import Model
from game_stack import GameStack
from twisted.spread import pb
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
    def __call__(self):
        self.game_stack.push(PlayerGuessGame(self.game_stack))

class PlayerGuessGame(Game):
    def on_push(self):
        self.model = self.game_stack.get_model("base game")
        current_player = self.model.players_order.get_next()
        current_word = self.model.word_order.get_next()
        if self.model.time_left < 5.0:
            self.model.time_left = 5.0
        time_left = self.model.time_left
        begin_turn_event = e.BeginTurnEvent(current_player, time_left, current_word)
        self.game_stack.post(begin_turn_event)
    def __call__(self, event):
        if isinstance(event, e.EndTurnEvent):
            if


def setup_catch_phrase(players, word_list, order):
    """
    returns event_manager for game

    players is a dictionary (client id: root_obj)
    word list is just a list of words
    """
    event_manager = GameEventManager(players)
    game_stack = GameStack(event_manager)
    event_manager.game_stack = game_stack
    model = Model(order, word_list)
    base_game = BaseGame(game_stack, model)
    game_stack.push(base_game, model, "base game")

    return event_manager
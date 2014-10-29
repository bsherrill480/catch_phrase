from basic_structures import Order
import random as sh
class Model:
    def __init__(self, players, world_list):
        """
        players is a list of client ids.
        """
        self.players_order = Order(players)
        self.word_order = Order(sh.shuffle(world_list))
        self.time_left = 30.0
        self.scores = {player:0 for player in players}
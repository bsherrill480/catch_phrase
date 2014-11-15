from basic_structures import Order
import random as sh
class Model:
    DEFAULT_TIME = 30.0
    def __init__(self, players, word_list, nicknames):

        """
        players is a list of client ids.
        """
        self.nicknames = nicknames
        print players
        for player in players:
            l2 = list(players)
            l2.remove(player)
            for player2 in l2:
                assert player != player2
        assert len(players) >= 1

        self.players_order = Order(players)
        sh.shuffle(word_list)
        self.word_order = Order(word_list)
        self.time_left = self.DEFAULT_TIME
        self.scores = {player:0 for player in players}
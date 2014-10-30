from basic_structures import Order
import random as sh
class Model:
    DEFAULT_TIME = 30.0
    def __init__(self, players, word_list):

        """
        players is a list of client ids.
        """

        #testing
        players = ['client1', 'client2']
        word_list = ["cat", "dog", "back", "in","town","didn't","care how"]
        #/testing

        for player in players:
            l2 = list(players)
            l2.remove(player)
            for player2 in l2:
                assert player != player2
        assert len(players) > 1

        self.players_order = Order(players)
        sh.shuffle(word_list)
        self.word_order = Order(word_list)
        self.time_left = self.DEFAULT_TIME
        self.scores = {player:0 for player in players}
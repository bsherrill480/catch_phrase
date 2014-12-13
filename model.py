from basic_structures import Order
import random as sh
class Model(object):
    def __init__(self, players, word_list, nicknames, round_time, leeway_time):

        """
        players is a list of client ids.
        word_list is the list of words
        nicknames is a dictionary of {client_id : client object}

        scores is a dictionary of {client_id: [score, nickname]}
        """
        self.nicknames = nicknames
        self.players_order = Order(players)
        sh.shuffle(word_list)
        self.word_order = Order(word_list)
        self.time_left = round_time
        self.scores = {player: [0, self.nicknames[player], player] for player in players}
        self.__nickname_scores = {}
        self.round_time = round_time
        self.leeway_time = leeway_time
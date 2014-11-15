"""
I made this for general use in making a game. So a lot of whats's here is
not ready yet.
"""

from random import shuffle as sh

class Card:
    def __init__(self):
        self.name = "generic card"
        self.picture = None


class Game:
    pass

class Board:
    """
    has display information.
    Use Zones.
    """
    def display(self):
        #make interact with kivy
        pass

class Zone:
    """
    places to put things. To help organize and check.
    """
    def __init__(self, obj = None, owner = None,pos = (0,0),):
        self.name = "zone"
        self.pos = pos
        self.obj = obj
        self.owner = owner

class Effect:
    """
    take in game_stack, changes game_stack
    """
    def __init__(self):
        pass
    def __call__(self, game_stack):
        pass
class Instruction:
    """
    waits for appropriate condition to apply effect
    """
    def __init__(self):
        self.effect = None
    def handle(self, game_stack, event):
        pass

#NOW PART OF GameStack
# class FieldInstructions:
#     """
#     contains all instructions currently in play. alerts
#     them to events.
#     """
#     def __init__(self, game_stack):
#         self.inst_list = []
#         self.game_stack = game_stack # so it can examine field too
#
#     def examine_and_pass(self, event):
#         #event.pass_through = True # already done in event
#         for instruction in self.instructions:
#             instruction.handle(event)
#         if event.pass_through: #if we didn't need to raise new event
#             if self.game_stack.size() >= 1:
#                 game = self.game_stack.peek()
#                 game(event)
#             else:
#                 raise Exception("Empty gamestack; no game to pass to")

class Pile(list):
    """
    Piles are almost python lists, just with a few new methods
    to make it more friendly to games.
    -
    """
    def add(self, *args):
        """
        adds arguments to pile.
        takes in an arbritrary number arguments if any are lists,
        flattens out list and adds each entry
        """

        def flatten_list(list):
            flat_list = []
            _recurse_flatten_list(list, flat_list)
            return flat_list

        def _recurse_flatten_list(remaining, flat_list):
            for item in remaining:
                if not isinstance(item, (list, tuple)):
                    flat_list.append(item)
                elif not (item == [] or item == tuple()): #if not empty list/tuple, append
                    _recurse_flatten_list(item, flat_list)

        self.extend(flatten_list(args))

    def shuffle(self):
        sh(self)

    def draw(self, num_cards = 1):
        if num_cards == 1:
            return self.pop()
        else:
            return [self.pop() for x in xrange(num_cards)]

class Player:
    def __init__(self, player_id):
        self.player_id = player_id

class Order:
    """
    This one is actually ready. Pretty simple class.
    Basically a circular list with a stack if you want dynamic adding to turns.
    also keeps track of who's current turn it is in current_player.
    """
    def __init__(self, order):
        """
        order is a non-emtpy list/tuple of players.
        order[0] goes first, order[1] goes second...
        Raises TypeError if not given list/tuple
        Raises ValueError if list/tuple is empty
        """
        if not isinstance(order, (tuple, list)):
            raise TypeError("Invalid type passed to Order, order must take " + \
                            "a list, tuple")
        if order == [] or order == tuple():
            raise ValueError("No empty lists/tuples")
        self.stack = []
        self._index = -1
        self._order = list(order) #incase was passed tuple
        self.current_player = order[0]

    def remove_player(self, player):
        """
        Only remove a player if he exists to this class.
        removes player from being called again.
        Does not change self.current_player.
        """
        self._order.remove(player)
        if player in self.stack:
            self.stack.remove(player)

    def __repr__(self):
        return "Order: " + str(self._order) + " Stack: " + str(self.stack)

    def get_next(self):
        """
        returns the next player and sets him to the current_player
        """
        if self.stack != []:
            self.current_player = self.stack.pop()
        else:
            self.current_player = self._next_in_list()
        return self.current_player

    def _next_in_list(self):
        """
        returns the next in _order and incriments _index appropritley
        so we can be circular
        """
        self._index = self._index + 1
        if self._index > (len(self._order) - 1):
            self._index = 0
        return self._order[self._index]


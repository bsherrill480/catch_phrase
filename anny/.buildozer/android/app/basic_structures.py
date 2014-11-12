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
    returns turn order in cyclic fashion

    """
    def __init__(self ,order):
        """
        order is a list player's of how turn order should go.
        on the last index, switches back to first index. can
        construct copy of passed order
        """
        #internals:
        #_stack is used to modify turn order
        self._stack = []
        self._index = -1
        self.order = order
        if isinstance(order, Order):
            self._stack = list(order._stack)#new copies
            self._index = order._index
            self.order = list(order.order)#new copies
        elif not isinstance(order, (tuple, list)):
            raise Exception("Invalid type passed to Order, order must take " + \
                            "a list or tuple")
        if self.order == []:
            raise Exception("No empty lists")
        self.current_player = order[0]
    def remove_player(self, id):
        self.order.remove(id)
        if id in self._stack:
            self._stack.remove(id)

    def __repr__(self):
        return str((self.order, self._stack))

    def get_next(self):
        if not (self._stack == []):
            self.current_player = self._stack.pop()
            return self.current_player
        self.current_player = self._next_in_list()
        return self.current_player

    def _next_in_list(self):
        self._index = self._index + 1
        if self._index > (len(self.order) - 1):
            self._index = 0
        return self.order[self._index]


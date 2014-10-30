from shared_events import TickEvent
from inspect import getargspec
from collections import deque

class GameStack:
    """
    Relies on Games to have __call__ method, with either takes either no arguments
    or takes 1 argument (an event)

    Note: queue is used for events, stack is used to place an event next in queue
    """
    def __init__(self, event_manager):
        self._game_stack = []
        self._game_stack_keys = []
        self.models = {}
        self.event_queue = deque()
        self.event_stack = []
        self.field_instructions = FieldInstructions(self)
        self.event_manager = event_manager
        self.__in_loop = False
        self.level = -1 # debugging
    def pop(self):
        """
        take off top element in stack, raises exception if stack is empty.
        Also deletes model at same level as game
        """
        if self.size() <= 0:
            raise Exception("Can not pop empty stack.")
        game = self._game_stack.pop()
        maybe_key = self._game_stack_keys.pop()
        if maybe_key:  # possibly popped a None, which implies no model exists
            del self.models[maybe_key]
        return game
    def push(self, game, model = None, model_key = None):
        """
        push a game. Optional to pass a model too, with optional model key for
        retrieval later. If no key is given (of if key passed is None), then depth
        (i.e. size of stack after push) is used as key.

        If no model is passed will try and call game.get_model_and_key(),
        but not crash if no method exits. game.get_model_and_key() must
        return model, model_key

        Raises exceptions: if key is an int (needed for internal use), if a key
        already is already in use, if given model_key without also a model.
        """
        if model_key and (not model): #i.e. model key with no model
            raise Exception("Model key without model")

        self._game_stack.append(game)
        if not model:
            try:
                model, model_key = game.get_model_and_key()
            except AttributeError:
                pass
        if isinstance(model_key, int):
            raise Exception("Int key are reserved for internal use")

        self._game_stack_keys.append(None)#append none first, will be updated if model was passed
        if model:
            self.add_model(model, model_key)

        #try on_push
        try:
            game.on_push()
        except AttributeError:
            pass


    def add_model(self, model, model_key=None):
        """
        *Could be tested more
        adds model at current level. optional model key for
        retrieval later. If no key is given (of if key passed is None), then depth
        (i.e. size of stack after push) is used as key.
        """
        if self.size() == 0:
            raise Exception("Empty stack; no model to add to")
        if self._game_stack_keys[-1]:  # if there is a key not None here,
                                                # then a model was already given
            raise Exception("There already exists a model")
        if not model_key: # if model_key is None
            model_key = self.size()
        if model_key in self.models.keys():  # if the model key is already in use
            raise Exception("key already in use")
        self._game_stack_keys[-1] = model_key
        self.models[model_key] = model

    def notify(self, event):
        #USE FOR DEBUGGING
        # self.level = self.level + 1
        # print "gamestack; in_loop = " + str(self.__in_loop) + "; level = "+ str(self.level)
        # print "   " + event.name
        # print "   event_queue: " + str(self.event_queue)
        # print "   game_stack" + str(self._game_stack)

        is_tick_event = isinstance(event, TickEvent)
        if (not self.__in_loop) and is_tick_event:
            # print "   Tick event recieved, loop starting"
            self.__in_loop = True
            while len(self.event_queue) > 0:
                event = self.event_queue.popleft()#pop off front(to save memory)
                                  #p.s. a linked list would be awesome for this
                # print "   launching: " + event.name, " level = ", str(self.level)
                self._single_event_notify(event)
                while self.event_stack != []:
                    self._single_event_notify(self.event_stack.pop())
            #self.event_queue = deque()
            self.event_queue.clear()
            # print "loop ending"
            self.__in_loop = False
        elif not is_tick_event:
            # print "   appending, ", event.name
            self.event_queue.append(event)
        # print "   level decreasing"
        # self.level = self.level - 1

    def notify_stack(self, event):
        """
        for use by instructions to place an event immediatly after examened event
        """
        self.event_stack.append(event)
    def post(self, event):
        self.event_manager.remote_post(event)

    def _single_event_notify(self, event):

        self.field_instructions.examine(event) # modifies event and deciedes
                                        #  whether to pass it to game
        if event.pass_through:
            game = self.peek()
            #try passing event, if game doesn't take event pass no event

            num_args = len(getargspec(game.__call__).args)
            if num_args == 1: #i.e. only self, so it takes no args
                game()
            else: #num_args should be 2, which means it takes only 1 argument
                game(event)

            #REPLACED WITH getargspec for easier debugging
            # try:
            #     game(event)
            # except TypeError:
            #
            #     game()
            # except Exception, er:
            #     raise er
    def peek(self):
        """
        returns top of stack, without taking off top element. Returns
        None if stack is empty
        """
        if self.size() <= 0:
            raise Exception("Empty game stack, nothing to peek at")
        else:
            return self._game_stack[-1]

    def size(self):
        return len(self._game_stack)

    #All below unnecesary, because user can access attributes directly,
    #but I like using it
    def get_model(self, key):
        return self.models[key]

    def give_instruction(self, instruction):
        self.field_instructions.add(instruction)

class FieldInstructions:
    def __init__(self, game_stack):
        self.instructions = []
        self.game_stack = game_stack # so it can examine field too

    def add(self, instruction):
        self.instructions.append(instruction)

    def examine(self, event):
        #event.pass_through = True # already done in event
        for instruction in self.instructions:
            instruction.handle(self.game_stack, event)

# class EventManager:
#     """
#     No longer necesary, but will keep incase I deciede to change
#     to method that needs
#     local evm so events are handled in order of being notified.
#     """
#     def __init__(self, game_stack):
#         self.game_stack = game_stack
#     def notify(self, event):
#         #---REMOVE ON FINISH DEBUG
#         if not isinstance(event, e.TickEvent):
#             print event.name
#         #---REMOVE ON FINISH DEBUG
#         self.game_stack._single_event_notify(event)



# WITH QUEUE
# problematic because posting event from instruction is appended
# after any other events from call to game because we are in the
# loop and it is appended
# class EventManager:
#     """
#     local evm so events are handled in order of being notified.
#     """
#     def __init__(self, game_stack):
#         self.queue = []
#         self.game_stack = game_stack
#         self.in_loop = False
#     def notify(self, event):
#         self.queue.append(event)
#         if isinstance(event, e.TickEvent) and (not self.in_loop):
#         # possible (but unlikely) to recieve another tick event while
#         # still looping which would cause a double loop. use in_loop
#         # to prevent that.
#             self.in_loop = True
#             for event in self.queue:
#                 #---REMOVE ON FINISH DEBUG
#                 if not isinstance(event, e.TickEvent):
#                     print event.name
#                 #---REMOVE ON FINISH DEBUG
#                 self.game_stack._single_event_notify(event)
#
#             self.queue = []
#             self.in_loop = False


if __name__ == "__main__":
    a = GameStack()
    a.push("game","model", "key")
    a.push("game2")
    a.add_model("model2")
    print a._game_stack
    print a._game_stack_keys
    a.pop()
    print a._game_stack
    print a._game_stack_keys
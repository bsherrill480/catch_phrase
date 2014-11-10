from twisted.spread import pb
from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from catch_phrase_server_game import setup_catch_phrase
import events as e
import circle_graph as cg
from time import sleep


class Client:
    def __init__(self, root_obj, client_id, nickname):
        self.root_obj = root_obj
        self.client_id = client_id
        self.nickname = nickname


class ServerEventManager(pb.Root):
    def __init__(self):
        #NEW COMMENT IN SERVEREVENTMANAGER
        self.clients = {}
        self.total_clients = 0
        self.world_lists = {"animals": ["cat", "dog", "bird"],
                            "objects": ["lamp", "waterbottle", "fork"]}
        self.lobbys = {"d_game": Lobby(self, self.world_lists["animals"])}
        self.total_games = 0
        self.looping_call = None

    def remote_register_client(self, root_obj, client_nickname):
        """
        returns True if client_id is accepted, returns False
        if client_id was already in use
        """
        assert client_nickname != ""
        client_id = "Client" + str(self.total_clients)
        self.total_clients = self.total_clients + 1
        self.clients[client_id] = Client(root_obj, client_id, client_nickname)
        print client_id + " : ///nickname: " + client_nickname
        return client_id

    def remote_get_unique_game_id(self):
        return "Game" + str(self.total_games)

    def remote_make_game_lobby(self, lobby_id, word_list_id):
        if lobby_id in self.lobbys:
            return False
        else:
            self.lobbys[lobby_id] = Lobby(self, self.world_lists[word_list_id])
            self.total_games = self.total_games + 1
            return True

        #add failed to make game return

    def remote_join_lobby(self, client_id, lobby_id):
        """
        returns true if success and false if no game
        """
        # print "client_id: " + str(client_id) + " lobby_id: " + str(lobby_id)
        # print "lobby_id in lobbys: ", (lobby_id in self.lobbys)
        # print "lobby keys: ", self.lobbys.keys()

        #note: game is set to None before game starts => check game to see
        #if game has started
        if lobby_id not in self.lobbys or self.lobbys[lobby_id].game:
            # print "returning false. keys: ", lobby_id in self.lobbys, str(self.lobbys.keys())
            return None
        lobby = self.lobbys[lobby_id]
        lobby.new_player(self.clients[client_id])
        return lobby

    def remote_get_word_list_options(self):
        return self.world_lists.keys()

    # def remote_begin_game(self, lobby_id):
    #     #initiate game
    #     pass

    def remote_unregister_client(self, client_id):
        print "unregister_client called"
        if client_id in self.clients.keys():
            del self.clients[client_id]

    #untested
    def remote_post(self, event, client_id):
        event.originator = client_id
        print "Recieved ", event.name, " from ", client_id
        for client in self.clients.values():
            # client.callRemote("notify", event)
            self.try_client_notify(self, client, event)

    #untested
    def try_client_notify(self, client, event):
        """
        will return None if succeses,
        else returns nick_name
        """
        try:
            client.callRemote('notify', event)
        except pb.DeadReferenceError:
            #can be improved for large dicts? Or use better data struct?:
            #http://stackoverflow.com/questions/8023306/get-key-by-value-in-dictionary
            for key, value in self.clients.iteritems():
                if value is client:
                    nick_name = self.client_nicknames[key]
                    del self.clients[key]
                    del self.client_nicknames[key]
                    break


class Lobby(pb.Root):
    def __init__(self, server_evm, world_list):
        self.server = server_evm
        self.players = []
        self.waiting = [] # organized: [..., (id, nickname), ...]
        self.organizer = cg.Organizer()
        self.word_list = world_list
        self.game = None

    def remote_notify(self, event):
        self.notify(event)

    def new_player(self, player):
        """
        player is a client
        """
        self.players.append(player)
        self.organizer.make_and_give_node(player, player.client_id)
        self.waiting.append((player.client_id, player.nickname))
        self.new_lineup_event()

    def remove_client_from_waiting(self, client_id):
        """
        also notifies
        """
        for tup in self.waiting:
            #tuple is (player_id, player_nick)
            if tup[0] == client_id:
                self.waiting.remove(tup)
                self.new_lineup_event()
                break

    def notify(self, event):
        """
        updates model accordingly, then posts to all players

        use return to prevnet going through useless if.. elif.. elif.. else
        """
        print event.name
        if self.game:
            self.game.post(event)
        else:
            if isinstance(event, e.ToHandoffToEvent):
                print "is handoff event", [tup for tup in self.waiting]
                self.organizer.set_next(event.my_id, event.to_handoff_to)
                self.remove_client_from_waiting(event.my_id)
                print "sending out new lineup", [tup for tup in self.waiting]
                self.new_lineup_event()
                return
            elif isinstance(event, e.StartGameRequestEvent):
                if self.organizer.is_perfect_circle():
                    print "START GAME SUCCESS"
                    self.has_started = True
                    game_start_event = e.GameStartEvent()
                    self.post(game_start_event)
                    self.game = setup_catch_phrase(
                        self.players,
                        self.word_list,
                        self.organizer.client_id_lists()[0][0:-1]#visual_strings returns list
                    )
                    def tick_event_to_game():
                        self.game.post(e.TickEvent())
                    self.looping_call = LoopingCall(tick_event_to_game)
                    self.looping_call.start(2.0)
                    return
                elif self.waiting == []:
                    print "WRONG ORDERING"
                    self.post(e.WrongOrderingEvent(self.organizer.visual_strings()))
            self.post(event)

    def post(self, event):
        """
        posts event to all players
        clients/players same thing
        """
        dead_clients = []
        need_new_order_event = False
        for client in self.players:
            #TODO: INTEGRATE WITH try_client_notify
            try:
                client.root_obj.callRemote('notify', event)
            except pb.DeadReferenceError:
                need_new_order_event = True
                dead_clients.append(client)
                del self.server.clients[client.client_id]

        for client in dead_clients:
            self.players.remove(client)
            self.remove_client_from_waiting(client.client_id)
            self.organizer.delete_node(client.client_id)

        if need_new_order_event:
            self.new_lineup_event()
            if self.game:
                pass#do gameover event until implement leaving

    def new_lineup_event(self):
        self.post(e.NewPlayerLineupEvent([(player.client_id, player.nickname) for player in self.players],
                                         [nickname for client_id, nickname in self.waiting]))


root_obj = ServerEventManager()
factory = pb.PBServerFactory(root_obj)
reactor.listenTCP(8800, factory)
reactor.run()
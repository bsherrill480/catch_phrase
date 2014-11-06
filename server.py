from twisted.spread import pb
from twisted.internet import reactor
from catch_phrase_server_game import setup_catch_phrase
from shared_events import NewOrderEvent
from time import sleep

class ServerEventManager(pb.Root):
    def __init__(self):
        self.clients = {}
        self.client_nicknames = {}
        self.total_clients = 0
        self.lobbys = {"d_game": Lobby(self)}
        self.total_games = 0

        self.world_lists = {"animals": ["cat", "dog", "bird"],
                            "objects":["lamp","waterbottle","fork"]}

    def remote_register_client(self, client, client_nickname):
        """
        returns True if client_id is accepted, returns False
        if client_id was already in use
        """
        assert client_nickname != ""
        client_id = "Client" + str(self.total_clients)
        self.total_clients = self.total_clients + 1
        self.clients[client_id] = client
        self.client_nicknames[client_id] = client_nickname
        print client_id + " : ///nickname: " + client_nickname
        return client_id

    def remote_get_unique_game_id(self):
        return "Game" + str(self.total_games)

    def remote_make_game_lobby(self, lobby_id):
        self.lobbys[lobby_id] = (Lobby(self))
        self.total_games = self.total_games + 1
        #add failed to make game return

    def remote_join_lobby(self, client_id, lobby_id):
        """
        returns true if success and false if no game
        """
        # print "client_id: " + str(client_id) + " lobby_id: " + str(lobby_id)
        # print "lobby_id in lobbys: ", (lobby_id in self.lobbys)
        # print "lobby keys: ", self.lobbys.keys()

        if not (lobby_id in self.lobbys):
            # print "returning false. keys: ", lobby_id in self.lobbys, str(self.lobbys.keys())
            return False
        lobby = self.lobbys[lobby_id]
        lobby.order.append(self.client_nicknames[client_id])
        lobby.players.append(self.clients[client_id])
        new_order_event = NewOrderEvent(lobby.order)
        lobby.notify(new_order_event)
        # for client in lobby.players:
        #     #TODO: INTEGRATE WITH try_client_notify
        #     try:
        #         client.callRemote('notify', new_order_event)
        #     except pb.DeadReferenceError:
        #         print "dead reference in lobby"
        #         #can be improved for large dicts? Or use better data struct?:
        #         #http://stackoverflow.com/questions/8023306/get-key-by-value-in-dictionary
        #         for key, value in self.clients.iteritems():
        #             if value is client:
        #                 nick_name = self.client_nicknames[key]
        #                 del self.clients[key]
        #                 del self.client_nicknames[key]
        #                 lobby.order.remove(nick_name)
        #                 #lobby.players.remove(client)
        #                 break
        print lobby.players
        return True


    def remote_get_word_list_options(self):
        return self.world_lists.keys()

    # def remote_begin_game(self, lobby_id):
    #     #initiate game
    #     pass

    def remote_unregister_client(self, client_id):
        print "unregister_client called"
        if client_id in self.clients.keys():
            del self.clients[client_id]

    def remote_post(self, event, client_id):
        event.originator = client_id
        print "Recieved ", event.name, " from ", client_id
        for client in self.clients.values():
            # client.callRemote("notify", event)
            self.try_client_notify(self, client, event)

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
class Lobby:
    def __init__(self, server_evm, players = None, order = None,):
        if not players:
            players = []
        if not order:
            order = []
        self.server = server_evm
        self.can_join = True
        self.players = players
        self.order = order
        self.game = None
    def give_event(self, event):
        if self.game:
            self.game.remote_post(event)

    def notify(self, event):
        dead_clients = []
        for client in self.players:
            #TODO: INTEGRATE WITH try_client_notify
            try:
                client.callRemote('notify', event)
            except pb.DeadReferenceError:
                dead_clients.append(client)
                #can be improved for large dicts? Or use better data struct?:
                #http://stackoverflow.com/questions/8023306/get-key-by-value-in-dictionary
                for key, value in self.server.clients.iteritems():
                    if value is client:
                        nick_name = self.server.client_nicknames[key]
                        del self.server.clients[key]
                        del self.server.client_nicknames[key]
                        self.order.remove(nick_name)
                        break
        for client in dead_clients:
            self.players.remove(client)

root_obj = ServerEventManager()
factory = pb.PBServerFactory(root_obj)
reactor.listenTCP(8800, factory)
reactor.run()
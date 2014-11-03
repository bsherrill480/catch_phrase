from twisted.spread import pb
from twisted.internet import reactor
from shared_events import PlayerJoinedEvent
from time import sleep

class ServerEventManager(pb.Root):
    def __init__(self):
        self.clients = {}
        self.client_nicknames = {}
        self.total_clients = 0
        self.lobbys = {}
        self.total_games = 0

        self.world_lists = {"animals": ["cat", "dog", "bird"],
                            "objects":["lamp","waterbottle","fork"]}

    def remote_register_client(self, client, client_nickname):
        """
        returns True if client_id is accepted, returns False
        if client_id was already in use
        """
        client_id = "Client" + str(self.total_clients)
        self.total_clients = self.total_clients + 1
        self.clients[client_id] = client
        self.client_nicknames[client_id] = client_nickname
        print client_id + " : ///nickname: " + client_nickname
        return client_id

    def remote_get_unique_game_id(self):
        return "Game" + str(self.total_games)

    def remote_make_game_lobby(self, lobby_id):
        self.lobbys[lobby_id] = [] #empty list for no players in lobby
        self.total_games = self.total_games + 1

    def remote_join_lobby(self, client_id, lobby_id):
        player_joined_event = PlayerJoinedEvent(self.client_nicknames[client_id])
        players_in_lobby = self.lobbys[lobby_id]
        for client in players_in_lobby:
            self.clients[client].callRemote('notify', player_joined_event)
        self.lobbys[lobby_id].append(client_id) #add client to lobby

    def remote_get_word_list_options(self):
        return self.world_lists.keys()

    def remote_begin_game(self, lobby_id):
        #initiate game
        pass
    def remote_unregister_client(self, client_id):
        print "unregister_client called"
        if client_id in self.clients.keys():
            del self.clients[client_id]

    def remote_post(self, event, client_id):
        event.originator = client_id
        print "Recieved ", event.name, " from ", client_id
        for client in self.clients.values():
            client.callRemote("notify", event)




root_obj = ServerEventManager()
factory = pb.PBServerFactory(root_obj)
reactor.listenTCP(8800, factory)
reactor.run()
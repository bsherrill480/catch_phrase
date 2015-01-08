from twisted.spread import pb
from twisted.internet.task import LoopingCall
from catch_phrase_server_game import setup_catch_phrase
import events as e
import circle_graph as cg
from word_list_manager import WordManager
from time import sleep

#TODO: QUIT EVENT NOT WORKING, SCORE ACROSS OTHER DEVICES,
class Client:
    """
    client class. Has client's root object, id, and nickname.
    Added observer pattern. Must add yourself as an observer,
    and have notify_of_dead_client(client),
    if you wish to disconnect client
    """
    def __init__(self, root_obj, client_id, nickname):
        self.root_obj = root_obj
        self.client_id = client_id
        self.nickname = nickname
        self.observers = []
        self.number_sharing_device = 1
    def remove_client(self):
        print "all observers", self.observers
        for observer in self.observers:
            print observer
            observer.dead_client(self)

class ServerEventManager(pb.Root):
    def __init__(self):
        self.clients = {} #organized {client_id: client_obj}
        self.total_clients = 0
        self.world_lists = WordManager("free")#a dict with the words preloaded
        self.lobbys = {}
        self.total_game_requests = 0
        self.looping_call = LoopingCall(self.remote_post, e.CopyableEvent())
        self.looping_call.start(5.0)

    def dead_client(self, client):
        """
        removes client from dict of clients (self.clients)
        """
        del self.clients[client.client_id]

    def remote_get_word_list(self, word_list_name):
        return self.world_lists[word_list_name]


    def remote_register_client(self, root_obj, client_nickname):
        """
        returns True if is accepted, returns False
        returns emtpy string (False) if client passed emtpy string
        (figured it might help later. Either way it evaluates to false)
        """
        if client_nickname == "":
            return ""
        client_id = "Client" + str(self.total_clients)
        self.total_clients = self.total_clients + 1
        client = Client(root_obj, client_id, client_nickname)
        client.observers.append(self)#add self as observer
        self.clients[client_id] = client
        print client_id + " : ///nickname: " + client_nickname
        return client_id

    def remote_get_unique_game_id(self):
        """
        not <i>guaranteed</i> to be unique. But in practice
        it will be. Worst case scenario user gets a "game name in
        use" popup
        """
        game_name = "Game" + str(self.total_game_requests)
        if game_name in self.lobbys:
            for i in xrange(26):
                letter_name = game_name + chr(97 + i)
                if letter_name not in self.lobbys:
                    return letter_name
        self.total_game_requests = self.total_game_requests + 1
        return game_name #sorry bud, out of luck

    def remote_make_game_lobby(self, lobby_id, word_list, score_system_mode, num_teams, round_time, leeway_time):
        """
        returns false if lobby_id is in use. Assumes word_list_id
        will be correct. Don't fuck me over me.
        """

        if lobby_id in self.lobbys:
            return (False, "lobby id in use")
        elif not word_list:
            return (False, "word list is empty")
        else:
            if isinstance(word_list, str):#if it wasn't a local copy.
                word_list = self.world_lists[word_list]
            self.lobbys[lobby_id] = Lobby(self, word_list, lobby_id,
                                          score_system_mode, num_teams,
                                          round_time, leeway_time)
            return (True, "success")

    def remote_join_lobby(self, client_id, lobby_id):
        """
        returns the lobby (a root_obj) if success, else returns None
        """

        #note: game is set to None before game starts => check game to see
        #if game has started
        if lobby_id not in self.lobbys or self.lobbys[lobby_id].game:
            return None
        lobby = self.lobbys[lobby_id]
        lobby.new_player(self.clients[client_id])
        return lobby

    def remote_join_lobby_score(self, client_id, lobby_id):
        if lobby_id not in self.lobbys or self.lobbys[lobby_id].game:
            return None
        lobby = self.lobbys[lobby_id]
        lobby.new_player_score(self.clients[client_id])
        return lobby

    def remote_get_word_list_options(self):
        """
        returns name of all the word lists
        """
        return self.world_lists.keys()

    #untested
    def remote_post(self, event, client_id = ""):
        """
        attempts to notify all users of event. removes them if they
        are dead
        """
        #event.originator = client_id
        #print "Recieved ", event.name, " from ", client_id
        for client in self.clients.values():#don't itervalues; we're possibly changing dictionary
            try:
                client.root_obj.callRemote('notify', event)
            except pb.DeadReferenceError:
                print "calling client.remove_client() on: ", client.client_id, client.nickname
                client.remove_client()



class Lobby(pb.Root):
    """
    Lobby used before game is started. Also acts as proxy to
    game once game has started.
    """
    TEAM_SCORE_SYSTEM = "teams"
    INDIVIDUAL_SCORE_SYSTEM = "individual"
    def __init__(self, server_evm, world_list, lobby_id, score_system_mode,
                 num_of_teams, round_time, leeway_time):
        self.server = server_evm
        self.players = [] # [...,client object,...]
        self.waiting = [] # organized: [..., (id, nickname), ...]
        self.organizer = cg.Organizer() #see circle_graph. used
                        #to tell if we have a circle (clients are pointing
                        #correctly).
        self.player_observers = []
        self.word_list = world_list
        self.game = None
        self.lobby_id = lobby_id
        #setup [...[score, team_name, team_id]...]
        self.score_system_mode = score_system_mode
        self.num_of_teams = num_of_teams
        self.round_time = round_time
        self.leeway_time = leeway_time
    def setup_teams(self ):
        if self.score_system_mode == self.INDIVIDUAL_SCORE_SYSTEM:
            teams = [[0, player.nickname, player.client_id] for player in self.players]
        else:
            teams = [ [0,"team " + str(i),"team " + str(i) ] for i in range(1, self.num_of_teams + 1)]
        return teams

    def remote_notify(self, event):
        """
        so clients can do lobby.callRemote(notify, event) to give us an event.
        calls notify(event), see notify for more info.
        """
        self.notify(event)

    def dead_client(self, client):
        """
        used in client objects observers.
        """
        if not self.game: #i.e. if in game I don't care about keeping track
            self.new_lineup_event()#will take care of recognizing he's gone

    def new_player(self, player):
        """
        player is a client object. Adds the new player to the lobby.
        """
        self.players.append(player)
        player.observers.append(self)
        self.organizer.make_and_give_node(player, player.client_id)
        self.waiting.append((player.client_id, player.nickname))
        self.new_lineup_event()

        #set default number of people sharing device
        player.number_sharing_device = 1

    def new_player_score(self, player):
        print "new player observer", player.client_id, player.nickname
        self.player_observers.append(player)
        player.observers.append(self)

    def remove_client_from_waiting(self, client_id):
        """
        removes the client from the waiting list.
        """
        waiting_tup = None
        for tup in self.waiting:
            #tuple is (player_id, player_nick)
            if tup[0] == client_id:
                #why don't I remove tup here and broadcast
                #a new_player_lineup_event here? I know I'll
                #comeback and think that...
                #I was told it's bad pratice to remove while iterating
                waiting_tup = tup
                break
        if waiting_tup:
            self.waiting.remove(waiting_tup)
            self.new_lineup_event()

    def notify(self, event):
        """
        updates lobby accordingly if the event is relevant. Then posts to all players.
        If the game has started, funnels event into game.
        """
        if self.game:
            self.game.post(event)
            #self.obs_post(event)
        else:
            if isinstance(event, e.QuitEvent):
                client_id = event.client_id
                self.players.remove(self.server.clients[client_id])
                self.remove_client_from_waiting(client_id)
                self.organizer.delete_node(client_id)
                self.new_lineup_event()
            elif isinstance(event, e.ToHandoffToEvent):
                self.organizer.set_next(event.my_id, event.to_handoff_to)
                self.remove_client_from_waiting(event.my_id)
                self.new_lineup_event()
            elif isinstance(event, e.NumberSharingDeviceEvent):
                print "recieved: ", event.name
                self.server.clients[event.client_id].number_sharing_device = event.number_sharing_device
            elif isinstance(event, e.StartGameRequestEvent):
                self.post(e.CopyableEvent()) #make sure everyone is still here
                                            #(post handles if someone left)
                if self.organizer.is_perfect_circle() and len(self.players) > 0:
                    self.post(e.GameStartEvent(self.setup_teams()))
                    #SEE circle_graph.client_id_lists() to understand why indexing & slicing
                    player_id_list = self.organizer.client_id_lists()[0][0:-1]
                    self._setup_list_for_multiple_players(player_id_list)
                    self.game = setup_catch_phrase(
                        self.players,
                        self.word_list,
                        player_id_list,
                        self.game_over_callback,
                        self.round_time,
                        self.leeway_time,
                        self.player_observers
                    )
                elif self.waiting == []:
                    #was not an acceptable circle. If waiting is empty we should
                    #return cycles. If waiting is not empty, they should be able to
                    #figure out the game can't start while we're still waiting on people.
                    #
                    #but seriously don't send out WrongOrderingEvent if it's not emtpy
                    #because that takes the spot of the waiting_on_following_players_list
                    #or at least at time of writing, it does.
                    self.post(e.WrongOrderingEvent(self.organizer.visual_strings()))
            self.post(event) # sent to everyone!

    def _setup_list_for_multiple_players(self, player_list):
        """
        takes in a player_id list and adds appropriate duplications such that the number
        of appearences of id = number of peole sharing device
        """
        for player in self.players:
            number_of_insertions = player.number_sharing_device - 1
            if number_of_insertions > 0:
                index_of_id = player_list.index(player.client_id)
                for i in range(number_of_insertions):
                    player_list.insert(index_of_id, player.client_id)

    def post(self, event):
        """
        posts event to all players/clients. If someone(s) is(are) dead, removes
        them and updates everyone about our sad loss.
        """
        dead_clients = []
        for client in self.players:
            try:
                client.root_obj.callRemote('notify', event)
            except pb.DeadReferenceError:
                dead_clients.append(client)
        print "dead clients:",dead_clients
        for client in dead_clients:
            print "removing:", client
            self.players.remove(client)
            self.remove_client_from_waiting(client.client_id)
            self.organizer.delete_node(client.client_id)
        if dead_clients:
            self.new_lineup_event()
        self.obs_post(event)

    def obs_post(self, event):
        dead_clients = []
        for client in self.player_observers:
            try:
                client.root_obj.callRemote('notify', event)
            except pb.DeadReferenceError:
                dead_clients.append(client)
        for client in dead_clients:
            self.player_observers.remove(client)


    def game_over_callback(self):
        """
        callback to delete this lobby from server's lobbys dictionary
        """
        del self.server.lobbys[self.lobby_id]

    def new_lineup_event(self):
        """
        Either the players have changed or the waiting list has changed.
        Posts NewPlayerLineupEvent to everyone
        """
        self.post(e.NewPlayerLineupEvent([(player.client_id, player.nickname) for player in self.players],
                                         [nickname for client_id, nickname in self.waiting]))

if __name__ == "__main__":
    from twisted.internet import reactor
    root_obj = ServerEventManager()
    factory = pb.PBServerFactory(root_obj)
    reactor.listenTCP(8800, factory)
    reactor.run()
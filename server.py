from twisted.spread import pb
from twisted.internet import reactor

class ServerEventManager(pb.Root):
    def __init__(self):
        self.clients = {}

    def remote_register_client(self, client, client_id):
        """
        returns True if client_id is accepted, returns False
        if client_id was already in use
        """
        if client_id in self.clients.keys():
            return False
        self.clients[client_id] = client
        return True

    def remote_unregister_client(self, client_id):
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
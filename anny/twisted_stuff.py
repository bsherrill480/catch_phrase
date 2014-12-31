from twisted.internet import reactor
from twisted.spread import pb
from twisted.internet import defer

#TODO: UPDATE AND MAKE MORE USER FRIENDLY AND READABLE
class Uplink():
    """
    A class which provides access to the server.
    Must call before before register_evm:
    1) give_username_and_pass
    #recomended do first because give_root_object is usally a deffered
    2) give_root_object with a root object
    3) give_id
    """
    def __init__(self, evm):
        """
        Must pass ClientEventManager
        """
        self.root_obj = None
        self.evm = evm
        self.nickname = ""
        self.password = ""
        self.id = ""
        self.evm_registered = False
    def post(self, event):
        """
        Posts event to server (server will .notify(event)
        to all clients of event)
        """
        if self.root_obj: #insurance post is not called
            return self.root_obj.callRemote("post", event, self.id)

    def register_evm(self, result):
        """
        takes result so it can be used in deffered
        registers the event manager to server (lets server .notify(event)
        from server of events)
        """
        return self.root_obj.callRemote("register_client", self.evm, self.nickname)

    #TODO: refactor to get_id
    def give_id(self, result):
        """
        for getting id from server. Use in a callback.
        """
        self.id = result
        return result

    def give_nickname_and_password(self, nickname, password):
        """
        just like it says.
        """
        self.nickname = nickname
        self.password = password

    def give_root_obj(self, root_obj):
        """
        root_obj is server's root remotely referencable object.
        """
        self.root_obj = root_obj


class ClientEventManager(pb.Root):
    """
    channels events on client side. Is remotley referencable
    """
    def __init__(self):
        self.listeners = []

    def remote_notify(self, event):
        """
        notifies all local listeners of event. Can be called from server.
        """
        for listener in self.listeners:
            listener.notify(event)

    def register_listener(self, listener):
        """
        registers object as a listener for events
        """
        self.listeners.append(listener)

    def unregister_listener(self, listener):
        """
        unregisters object as a listener for events
        """
        self.listeners.remove(listener)
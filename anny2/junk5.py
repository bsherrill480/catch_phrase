# install_twisted_rector must be called before importing  and using the reactor
from kivy.support import install_twisted_reactor
install_twisted_reactor()

from twisted.internet import reactor
from twisted.internet import protocol
from twisted.spread import pb
from server import ServerEventManager as s_evm

class EchoProtocol(protocol.Protocol):
    def dataReceived(self, data):
        response = self.factory.app.handle_message(data)
        if response:
            self.transport.write(response)

class EchoFactory(protocol.Factory):
    protocol = EchoProtocol
    def __init__(self, app):
        self.app = app


from kivy.app import App
from kivy.uix.label import Label

class TwistedServerApp(App):
    def build(self):
        self.label = Label(text="server started\n")
        root_obj = s_evm()
        factory = pb.PBServerFactory(root_obj)
        my_port = 6834
        reactor.listenTCP(my_port, factory)
        return self.label

    def handle_message(self, msg):
        self.label.text  = "received:  %s\n" % msg

        if msg == "ping":  msg =  "pong"
        if msg == "plop":  msg = "kivy rocks"
        self.label.text += "responded: %s\n" % msg
        return msg


if __name__ == '__main__':

    TwistedServerApp().run()

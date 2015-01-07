from twisted.internet import protocol
from twisted.internet import reactor
my_version = "1.0"
class IperClient(protocol.Protocol):

    def connectionMade(self):
        print "writing"
        self.transport.write(" ")

    def dataReceived(self, recieved_data):
        self.transport.loseConnection()
        print "data recieved"

class IperFactory(protocol.ClientFactory):
    def buildProtocol(self, addr):
        print "built"
        return IperClient()

    def clientConnectionFailed(self, connector, reason):
        print "connection failed"
reactor.connectTCP("ec2-54-69-136-104.us-west-2.compute.amazonaws.com", 8000, IperFactory())
reactor.run()
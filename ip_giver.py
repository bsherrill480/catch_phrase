from twisted.internet import protocol, reactor

ip = "localhost"
port = 8800
class GiveIp(protocol.Protocol):
    def dataReceived(self, data):
        self.transport.write(str(ip) + " " + str(port))

class GiveIpFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return GiveIp()
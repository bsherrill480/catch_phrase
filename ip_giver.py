from twisted.internet import protocol, reactor

ip = "localhost"
server_port = 8800
current_version = "1.0"
class GiveIp(protocol.Protocol):
    def dataReceived(self, data):
        self.transport.write(str(ip) + " " + str(server_port) + " " + str(current_version))
        #self.transport.write((ip, port, current_version))

class GiveIpFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return GiveIp()
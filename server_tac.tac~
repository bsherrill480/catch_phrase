from server import ServerEventManager
from twisted.application import internet, service
from twisted.spread import pb

serverfactory = pb.PBServerFactory(ServerEventManager())
application = service.Application("server")
ServerService = internet.TCPServer(8800, serverfactory)
ServerService.setServiceParent(application)
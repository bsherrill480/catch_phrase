from server import ServerEventManager
from twisted.application import internet, service
from twisted.spread import pb

server_evm = ServerEventManager()
server_evm.begin_logging()
serverfactory = pb.PBServerFactory(server_evm)
application = service.Application("server")
ServerService = internet.TCPServer(8800, serverfactory)
ServerService.setServiceParent(application)

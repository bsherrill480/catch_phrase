from twisted.application import internet, service
from ip_giver import GiveIpFactory

my_port = 8000

application = service.Application("giveip")
giveipService = internet.TCPServer(my_port, GiveIpFactory())
giveipService.setServiceParent(application)
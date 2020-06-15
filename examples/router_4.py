from router import Router

config = {'host_id': 'localhost', 'port_id': 4004, 'server_buffer': 1024, 'server_max_queue': 10}
connections = [('localhost', 4002), ('localhost', 4003)]
yea = Router(config = config, connections = connections, address_id = 'd')
yea.start()
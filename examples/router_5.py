from router import Router

config = {'host_id': 'localhost', 'port_id': 4005, 'server_buffer': 1024, 'server_max_queue': 10}
connections = [('localhost', 4002), ('localhost', 4004), ('localhost', 4007)]
yea = Router(config = config, connections = connections, address_id = 'e')
yea.start()
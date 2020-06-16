from router import Router

config = {'host_id': 'localhost', 'port_id': 4008, 'server_buffer': 1024, 'server_max_queue': 10}
connections = [('localhost', 4004), ('localhost', 4006), ('localhost', 4007), ('localhost', 4009)]
yea = Router(config = config, connections = connections, address_id = 'h')
yea.start()
from router import Router

config = {'host_id': 'localhost', 'port_id': 4003, 'server_buffer': 1024, 'server_max_queue': 10}
connections = [('localhost', 4001), ('localhost', 4002), ('localhost', 4004), ('localhost', 4006)]
yea = Router(config = config, connections = connections, address_id = 'c')
yea.start()
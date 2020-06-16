from router import Router

config = {'host_id': 'localhost', 'port_id': 4006, 'server_buffer': 1024, 'server_max_queue': 10}
connections = [('localhost', 4003), ('localhost', 4004), ('localhost', 4008)]
yea = Router(config = config, connections = connections, address_id = 'f')
yea.start()
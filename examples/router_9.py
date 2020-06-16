from router import Router

config = {'host_id': 'localhost', 'port_id': 4009, 'server_buffer': 1024, 'server_max_queue': 10}
connections = [('localhost', 4007), ('localhost', 4008)]
yea = Router(config = config, connections = connections, address_id = 'i')
yea.start()
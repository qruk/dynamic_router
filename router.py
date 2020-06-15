from communication import Communication
from time import time

# Класс маршрутизатора 
class Router:
	# Собственный адрес маршрутизатора (любой строковый идентификатор), на который будут пересылаться пакеты и который будет находится в таблице маршрутизации другого роутера
	address_id = None

	# Таблица маршрутизации {address_id1: {port1: ping1, port2: ping2, ...}, address_id2:...}
	router_table = {}

	# Cловарь порт-объект порта
	ports = {}

	# Список доступных соединений [(host1, port1), (host2, port2), ...]	
	# Абстракция физических (проводных) соединений
	connections = []

	# Конфигурация серверной части маршрутизатора
	# config = {port_id: str, host_id: int, server_buffer: int, server_max_queue: int}
	config = {}

	def __init__(self, config, connections, address_id = None):
		self.config = config
		self.connections = connections
		self.address_id = self.router(address_id)
		print('Я проснулся!', self.address_id)
		self.communication = Communication(self)	

	def __str__(self):
		return ( str(self.config['host_id']) + ':' + str(self.config['port_id']) )

	def router(self, address_id):
		if not address_id:
			time_id = str('{:.9f}'.format( time() )).split('.')
			return time_id[1][-3:] + '.' + time_id[1][-6:-3] + '.' + time_id[1][-9:-6] + '.' + time_id[0][:3]
		else:
			return address_id if ( type(address_id) is str ) else str(address_id)

	def start(self):
		self.communication.start()


# @todo взвешенные ребра по времени

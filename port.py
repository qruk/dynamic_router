from socket import AF_INET, SOCK_STREAM
from connection import ClientConnection
from enum import Enum

# Класс соединения клиент-сервер (TCP)
class ClientConnectionTCP(ClientConnection):

	client_family = AF_INET
	client_type = SOCK_STREAM

# Класс-перечисление состояний маршрутизатора, подключенных к порту
class PortState(Enum):
	dead = 0
	alive = 1
	resurrecting = 2

# @todo коллбеки
# Класс соединения маршрутизатора через порт
class Port:

	state = PortState.dead

	def __init__(self, host, port, client_buffer = 1024):
		self.port = port # Порт сервера
		self.host = host # Хост клиента
		self.client_buffer = client_buffer

	def __str__(self):
		return (str(self.host) + ':' + str(self.port))

	# Подключение к маршрутизатору
	def enable(self):
		self.state = PortState.resurrecting
		try:
			self.client = ClientConnectionTCP(client_host = self.host, client_port = self.port, client_buffer = self.client_buffer)	
		except:
			self.state = PortState.dead
			return ('FAILED: Connection on {router}'.format(router= str(self)))

		self.state = PortState.alive
		return None

	def disable(self):
		if self.client:
			del self.client
		self.state = PortState.dead

	# Отправка сообщения на маршрутизатор
	def send(self, message):
		try:
			self.client.send(  message  )
			return None
		except:
			return ('FAILED: sending message on {router}'.format(router = str(self)))

	def recv(self):
		try:
			return self.client.recv()
		except:
			return None

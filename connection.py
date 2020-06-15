from socket_impl import SocketImpl
from threading import Thread

# Класс соединения клиент-сервер
class ServerConnection:

	server_family = None
	server_type = None
	level = None
	optname = None
	value = None

	def __init__(self, server_host, server_port, server_buffer, server_max_queue):
		self.socket = SocketImpl(sock_family = self.server_family, sock_type = self.server_type, sock_host = server_host, sock_port = server_port, sock_buffer = server_buffer)

		if (self.level and self.optname and self.value):
			self.socket.setsockopt(self.level, self.optname, self.value)

		self.socket.bind()
		self.socket.listen(server_max_queue)

	def run(self, handle, sock_buffer = 1024, **kwargs):
		while True:
			(sock, address) = self.socket.accept()
			sock_impl = SocketImpl(sock = sock, sock_host = address[0], sock_port = address[1], sock_buffer = sock_buffer)
			thread = Thread(target=handle, args=(sock_impl, kwargs)) if kwargs else Thread(target=handle, args=(sock_impl,))
			thread.daemon = True
			thread.start()

class ClientConnection:

	client_family = None
	client_type = None

	def __init__(self, client_host, client_port, client_buffer):
		self.socket = SocketImpl(sock_family = self.client_family, sock_type = self.client_type, sock_host = client_host, sock_port = client_port, sock_buffer = client_buffer)
		self.socket.connect()

	def send(self, message):
		self.socket.send(message)

	def recv(self):
		return self.socket.recv()
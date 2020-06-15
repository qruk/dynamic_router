from socket import socket
from signal import signal, SIGINT
from sys import exit

# Класс интерфейса сокета
class SocketImpl:

	def __init__(self, sock_host, sock_port, sock_buffer, sock = None, sock_family = None, sock_type = None, sock_code = 'utf-8'):
		self.sock_host = sock_host
		self.sock_port = sock_port
		self.sock_buffer = sock_buffer

		if sock:
			self.sock_family = sock.family
			self.sock_type = sock.type
			self.sock = sock
		else:
			self.sock_family = sock_family
			self.sock_type = sock_type
			self.sock = self.socket()

		self.sock_code = sock_code

	def __del__(self):
		self.close()

	def socket(self):
		return socket() if( self.sock_family and self.sock_type ) else socket(self.sock_family, self.sock_type)

	def connect(self):
		self.sock.connect((self.sock_host, self.sock_port))

	def close(self):
		self.sock.close()

	def send(self, message):
		self.sock.send( message.encode(self.sock_code) )

	def sendall(self):
		self.sock.sendall( message.encode(self.sock_code) )

	def recv(self):
		message = self.sock.recv( self.sock_buffer )
		return message.decode(self.sock_code)

	def bind(self):
		self.sock.bind((self.sock_host, self.sock_port))

	def listen(self, sock_max_queue):
		self.sock.listen(sock_max_queue)

	def accept(self):
		signal(SIGINT, self.interrupt)
		(sock, address) = self.sock.accept()
		return (sock, address)

	def setsockopt(self, level, optname, value):
		self.sock.setsockopt(level, optname, value)

	def shutdown(self, how):
		self.sock.shutdown(how)

	def interrupt(self, *args):
		print ('\nstop working...')
		self.close()
		exit(0)

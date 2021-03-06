from enum import Enum
from port import Port, PortState
from connection import ServerConnection
from socket import AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR, SHUT_RDWR
from time import sleep, time
from threading import Thread, RLock
from json import dumps, loads

from random import choice

# Класс-перечисление различных типов сообщений
class MessageType(Enum):
	hello = 0
	dead  = 1
	data = 2

# Класс соединения сервер-клиент (TCP)
class ServerConnectionTCP(ServerConnection):

	server_family = AF_INET
	server_type = SOCK_STREAM
	level = SOL_SOCKET
	optname = SO_REUSEADDR
	value = 1

# @todo class обернуть порты в class Neighbors, а работу с полями роутера - в RouterImpl (в т.ч. мьютексы), base_delay, incr_delay
# Класс, определяющий поведение маршрутизатора: следит за состоянием других маршрутизаторов на портах, перенаправляет пакеты на нужные порты, актуализирует свою таблицу маршрутизации и тд @todo dynamicComunication?
class Communication:

	def __init__(self, router):
		self.router = router
		self.server = ServerConnectionTCP(server_host = self.router.config['host_id'], server_port = self.router.config['port_id'], server_buffer = self.router.config['server_buffer'], server_max_queue = self.router.config['server_max_queue']) 
		self.router_table_lock = RLock()
		self.port_locks = {}
		self.log_lock = RLock()
		self.enable_ports()
		# @todo 
		self.neighbor_delay = 1;

	def get_port_id(self):
		return ( str(self.router.config['host_id']) + ':' + str(self.router.config['port_id']) )

	def is_mine(self, address):
		return ((address == self.router.address_id) or (not address))

	def is_port_alive(self, port):
		return self.router.ports[port].state is PortState.alive

	def make_thread(self, target, args = None, daemon = False):
		thread = Thread(target = target, args=args) if args else Thread(target = target)
		thread.daemon = daemon
		thread.start()
		return thread

	def write_to_file(self, file, data, locker):
		locker.acquire()
		try:
			f = open(file, 'a', encoding='utf-8')
			f.write(str(data) + '\n')
			f.close()
		except Exception as e:
			print("FAILED: writing to file: {e}".format(e = e))
		finally:
			locker.release()

	# Ведение лог-файла
	def log(self, callback):
		self.make_thread( target = self.write_to_file, args = (self.get_port_id(), callback, self.log_lock), daemon = True )

	# Прием конечного сообщения от других клиентов
	def recv(self, data):
		self.make_thread( target = self.write_to_file, args = (self.get_port_id() + '_data', data, self.log_lock), daemon = True )

	# Метод, устанавливающий соединение на порте
	def get_up_port(self, port):
		self.port_locks[port].acquire()
		try:
			callback = self.router.ports[port].enable()
		except Exception as e:
			self.log('FAILED: {port} can not get up: {e}'.format(port=port, e = e))
		finally:
			self.port_locks[port].release()
		self.log('CONNECTED: {router}'.format(router = str(self.router.ports[port])) if not callback else callback)
		return True if not callback else False

	# Метод, закрывающий соединение на порте
	def turn_off_port(self, port):
		self.port_locks[port].acquire()
		try:
			self.router.ports[port].disable()
		except Exception as e:
			self.log('FAILED: {port} broken and can not be closed: {e}'.format(port=port, e = e))
		finally:
			self.port_locks[port].release()

	# Метод инициализации портов и попытки установления соединения на них
	def enable_ports(self):
		for host, port in self.router.connections:
			new_port = Port(port = port, host = host)
			new_port_name = str(new_port)
			self.router.ports.update({new_port_name: new_port})
			self.port_locks.update({new_port_name: RLock()})

		for port in self.router.ports.keys():
			self.get_up_port(port)

	# Эти 2 метода инкапсулируют тот факт, что сообщение получается не от порта, а от клиента с допустимым id порта сервера
	def pack_message(self, message_sender, message_address, message_type, message_data, message_delay):
		package = {'port_id': self.get_port_id(), 'message_sender': message_sender, 'message_address': message_address, 'message_type': message_type, 'message_data': message_data, 'message_delay': message_delay }
		return dumps(package)

	def unpack_message(self, package):
		message = loads(package)
		port = message.pop('port_id') 
		return (port, message)

	# Метод паковки сообщениz
	def make_package(self, message_sender, message_address, message_type, message_data, message_delay):
		if message_type is MessageType.hello:
			return self.pack_message(message_sender = message_sender, message_address = message_address, message_type = message_type.value, message_data = self.router.router_table, message_delay = message_delay)
		elif message_type is MessageType.data:
			return self.pack_message(message_sender = message_sender, message_address = message_address, message_type = message_type.value, message_data = message_data, message_delay = message_delay)
		elif message_type is MessageType.dead:
			return self.pack_message(message_sender = message_sender, message_address = message_address, message_type = message_type.value, message_data = message_data, message_delay = message_delay)
		else:
			return None

	# Метод получения сообщения с порта
	def get_message (self, package):
		try:
			(port, message) = self.unpack_message(package)
			sender = message.pop('message_sender')
			address = message.pop('message_address')
			message['message_type'] = MessageType(message['message_type'])
			return (port, sender, address, message)
		except Exception as e:
			self.log("FAILED: getting message from port: {e}".format(e = e))
			return None

	# Методы работы с таблицей маршрутизации
	def get_router_table_view(self):
		self.router_table_lock.acquire()
		try:
			return str(self.router.router_table)
		except Exception as e:
			self.log("FAILED: getting view of router table: {e}".format(e = e))
			return None
		finally:
			self.router_table_lock.release()

	# Удаление адреса из таблицы маршрутизации
	def delete_address_from_router_table(self, address):
		self.router_table_lock.acquire()
		result = None
		try:
			result = self.router.router_table.pop(address, None)
		except Exception as e:
			self.log("FAILED: delete address from router table: {e}".format(e = e))
		finally:
			self.router_table_lock.release()
		return result

	# Отправка dead-пакета
	def send_dead_message(self, port, data):
		self.send_message(message_type = MessageType.dead, message_sender = self.router.address_id, message_data = data, specific_port = port)

	# Отправка dead-пакетов на все адреса to thread
	def deader(self, address):
		for port in self.router.ports.keys():
				if self.is_port_alive(port):
					self.send_dead_message(port, address)

	# Удаляет порт из адресной строки, оповещает всех о недостижимости, если у адреса больше нет портов
	def delete_port_from_address(self, port, address):
		self.router_table_lock.acquire()
		try:
			ports = self.router.router_table.get(address)
			if ports:
				delay = ports.pop(port, None)
				if delay:
					if not self.router.router_table[address]:
						self.delete_address_from_router_table(address)
						self.make_thread (target = self.deader, args = (address,), daemon = True)
		except Exception as e:
			self.log("FAILED: delete port from address in router table: {e}".format(e = e))
		finally:
			self.router_table_lock.release()

	# Метод удаления порта из таблицы паршрутизации, если у адреса больше нет портов, то он удаляетя из таблицы и всем рассылается запрос о его недостижимости
	def delete_port_from_router_table(self, port):
		self.router_table_lock.acquire()
		try:
			non_reachable_addresses = []
			for address, ports in self.router.router_table.items():
				delay = ports.pop(port, None)
					
				if not self.router.router_table[address]:
					non_reachable_addresses.append(address)

			for address in non_reachable_addresses:
				self.delete_address_from_router_table(address)
				# Оповещаем всех, что cоединения к этому адресу больше нет
				self.make_thread (target = self.deader, args = (address,), daemon = True)
		except Exception as e:
			self.log("FAILED: delete port from router table: {e}".format(e = e))
		finally:
			self.router_table_lock.release()

	# Метод удаления порта из таблицы и перевода его в неактивный режим
	def delete_port(self, port):
		self.turn_off_port(port)
		self.delete_port_from_router_table(port)
		self.log('DISCONNECTED: {port}'.format(port = port))

	# Метод добавления порта с задержкой в таблицу
	def add_address(self, address, port_delay):
		self.router_table_lock.acquire()
		try:
			self.router.router_table.update({address: port_delay})
			return None
		except Exception as e:
			return 'adding {address} to router table failed: {e}'.format(address = address, e = e)
		finally:
			self.router_table_lock.release()

	# Обновить задержку до адреса по порту, а так же обновить таблицу соседей
	def update_delay(self, address, port, delay):
		self.router_table_lock.acquire()
		try:
			ports = self.router.router_table.get(address)
			max_delay = max(self.router.router_table[address].values()) if ports else None
		except Exception as e:
			self.log('FAILED: {address} not updated: {e}'.format(address  = address, e = e ))
		finally:
			self.router_table_lock.release()

		if max_delay:
			if delay == max_delay:
				ports.update({port: delay})
			elif delay < max_delay:
				callback = self.add_address(address, {port: delay})
				#print ('UPDATED: {address}'.format(address  = address ))
			else:
				pass
		else:
			callback = self.add_address(address, {port: delay})
			#print ('ADDED: {address}'.format(address  = address ) if not callback else 'FAIED: ' + callback)		

	# Метод обновления таблицы маршрутизации с помощью таблицы маршрутизации "соседа"
	def update_router_table(self, table, port):
		self.router_table_lock.acquire()
		try:
			# Не смотрим на свой адресс
			table.pop(self.router.address_id, None)

			for address, ports in table.items():
				delay = min(ports.values()) + self.neighbor_delay
				self.update_delay(address = address, port = port, delay = delay)

		except Exception as e:
			self.log('FAILED: table from {port} not updated by {table}: {e}'.format(port = port, table = table, e = e))
		finally:
			self.router_table_lock.release()

	# Возвращает порт c минимальной задержкой по адресу
	def get_min_port(self, address):
		self.router_table_lock.acquire()
		try:
			delays_of_ports = self.router.router_table.get(address)
			port = None if not delays_of_ports else min(delays_of_ports, key=lambda unit: delays_of_ports[unit])
		except Exception as e:
			self.log('FAILED: no ports to {address}: {e}'.format(address  = address, e = e ))
			return None
		finally:
			self.router_table_lock.release()
		return port

	# Возвращает задержку по порту
	def get_delay(self, address, port):
		self.router_table_lock.acquire()
		try:
			delays_of_ports = self.router.router_table.get(address)
			delay = delays_of_ports.get(port)
		except Exception as e:
			self.log('FAILED: no delay to {address}-{port}: {e}'.format(address = address, port = port, e = e))
			return None
		finally:
			self.router_table_lock.release()
		return delay

	# Метод отправки (с повторами, если порт еще подключается), если отправка невозможна впринципе - удаляет порт из таблицы маршрутизации и переводит его в состояние "мертв"
	def try_send(self, port, package, counter = 3):
		if not port:
			print(package)
			print(counter)
		port_state = self.router.ports[port].state

		if port_state is PortState.alive:
			callback = self.router.ports[port].send( package )
			if callback:
				self.delete_port(port);
				self.log(callback)
				return False
			return True

		elif port_state is PortState.resurrecting:
			if (counter <= 0):
				self.delete_port(port);
				self.log('FAILED: sending time out')
				return False
			sleep(0.1)
			self.try_send(port, package, counter - 1)

		else:
			pass

	# Метод непосредственной отправки сообщения, обновляет таблицу маршрутизации в случае успешного хеллоу-запроса
	def send_message(self, message_sender, message_type, message_address = None, message_data = None, message_delay = 1, specific_port = None):
		port = self.get_min_port(address = message_address) if not specific_port else specific_port
		package = self.make_package(message_sender = message_sender, message_address = message_address, message_type = message_type, message_data = message_data, message_delay = message_delay)
		self.make_thread ( target = self.try_send, args = (port, package) )

	# Отправка клиентских запросов
	def send_client_message(self):
		#address = input("address: ")
		#message = input("message: ")
		adresses = list ( self.router.router_table.keys() )
		if not adresses:
			return
		address = choice( adresses )
		message = 'client message from ' + self.router.address_id
		self.send_message(message_sender = self.router.address_id, message_address = address, message_type = MessageType.data, message_data = message)

	def clienter(self):
		while True:
			self.send_client_message()
			sleep(1)

	# Отправка hello-пакетов
	def send_hello_message(self, port):
		self.send_message(message_type = MessageType.hello, message_sender = self.router.address_id, specific_port = port)

	def hellower(self):
		while True:
			for port in self.router.ports.keys():
				if self.is_port_alive(port):
					self.send_hello_message(port)
			sleep(3)

	# Прием сообщений на маршрутизатор
	def recv_message(self, package):
		try:
			(port, sender, address, message) = self.get_message(package)
		except Exception as e:
			self.log("FAILED: recieving message: {e}".format(e = e))
			return False
		
		if self.is_mine(sender):
			# Если "круг замкнулся" - игнорируем пакет
			return True

		if not self.is_port_alive(port):
			self.get_up_port(port)

		if self.is_mine(address):
			# Сохраняем пакеты
			self.accept_message(message_sender = sender, message_type = message['message_type'], message_data = message['message_data'], message_delay = message['message_delay'], message_port = port)

		else:
			# Отправляем дальше
			self.send_message(message_sender = sender, message_address = address, message_type = message['message_type'], message_data = message['message_data'], message_delay = message['message_delay'] + self.neighbor_delay )#self.get_delay(address, port) )

		return True

	def accept_message(self, message_sender, message_type, message_data, message_delay, message_port):
		if message_type is MessageType.hello:
			# @ todo проверка на соседа, проверка на удаление узлов у других таблиц
			self.update_delay(address = message_sender, port = message_port, delay = message_delay) 
			self.update_router_table(table = message_data, port = message_port)
			self.log('ROUTER TABLE: {table}'.format(table = self.get_router_table_view()))
		elif message_type is MessageType.dead:
			self.delete_port_from_address(message_port, message_data)
			self.log('ROUTER TABLE: {table}'.format(table = self.get_router_table_view()))
		elif message_type is MessageType.data:
			self.recv(message_data)
		else:
			pass

	def handle(self, client):
		while True:
			package = client.recv()
			result = self.recv_message(package)
			if not result:
				client.shutdown(SHUT_RDWR)
				client.close()
				break


	# Запуск маршрутизатора
	def start(self):
		self.make_thread(target = self.clienter, daemon = True)
		self.make_thread(target = self.hellower, daemon = True)
		self.server.run(self.handle)

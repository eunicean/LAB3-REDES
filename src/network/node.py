import socket
import threading
import json
import time
from src.utils.logger import setup_logger

class Node:
    def __init__(self, node_id, neighbors, host, port, routing_algorithm):
        self.node_id = node_id
        self.neighbors = neighbors
        self.host = host
        self.port = port
        self.routing_algorithm = routing_algorithm
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_sockets = {}
        self.logger = setup_logger(node_id)
        self.running = True
        
        self.routing_algorithm.set_node(self)

    def start_server(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.logger.info(f"Escuchando en {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, addr = self.server_socket.accept()
                    threading.Thread(target=self.handle_client, 
                                    args=(client_socket,)).start()
                except Exception as e:
                    if self.running:
                        self.logger.debug(f"Error aceptando conexión: {e}")
        except Exception as e:
            self.logger.error(f"Error iniciando servidor: {e}")

    # Intenta conectar a vecinos, pero sin bloquear ni fallar si no están disponibles
    def connect_to_neighbors(self, node_addresses):
        for neighbor_id in self.neighbors:
            if neighbor_id in node_addresses:
                threading.Thread(target=self.try_connect, 
                               args=(neighbor_id, node_addresses[neighbor_id])).start()

    #Intenta conectar a un vecino con reintentos en segundo plano
    def try_connect(self, neighbor_id, address):
        host, port_str = address.split(':')
        port = int(port_str)
        
        while self.running:
            try:
                if neighbor_id in self.client_sockets:
                    # Ya conectado, verificar si la conexión sigue activa
                    try:
                        # Enviar un ping simple para verificar conexión
                        ping_msg = json.dumps({
                            "proto": "flooding",
                            "type": "hello",
                            "from": self.node_id,
                            "to": neighbor_id,
                            "ttl": 1,
                            "headers": [],
                            "payload": "ping"
                        })
                        self.client_sockets[neighbor_id].send(ping_msg.encode())
                    except:
                        # Conexión perdida, eliminar y reconectar
                        if neighbor_id in self.client_sockets:
                            del self.client_sockets[neighbor_id]
                
                if neighbor_id not in self.client_sockets:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(2)
                    sock.connect((host, port))
                    self.client_sockets[neighbor_id] = sock
                    self.logger.info(f"Conectado a {neighbor_id} en {host}:{port}")
                
                # Conexión exitosa, salir del bucle de reintentos
                break
                
            except Exception as e:
                self.logger.debug(f"No se pudo conectar a {neighbor_id}: {e}")
                time.sleep(3)  # Reintentar después de 3 segundos

    def handle_client(self, client_socket):
        try:
            data = client_socket.recv(4096).decode()
            if not data:
                return
                
            message = json.loads(data)
            self.logger.info(f"Mensaje recibido: {message}")
            
            # Procesar el mensaje según el protocolo estándar
            self.process_standard_message(message)
            
        except json.JSONDecodeError:
            self.logger.error("Mensaje JSON mal formado")
        except Exception as e:
            self.logger.error(f"Error manejando cliente: {e}")
        finally:
            # No cerramos el socket para mantener la conexión
            pass

    #Procesa mensajes según el protocolo definido
    def process_standard_message(self, message):
        message_type = message.get("type", "")
        
        if message_type == "hello":
            # Mensaje de saludo/keepalive, podemos responder
            self.logger.debug(f"Hello recibido de {message.get('from')}")
        else:
            # Delegar al algoritmo de routing
            self.routing_algorithm.handle_message(message)

    #Envía mensaje usando el protocolo estándar
    def send_message(self, message, neighbor_id):
        try:
            if neighbor_id in self.client_sockets:
                sock = self.client_sockets[neighbor_id]
                sock.send(json.dumps(message).encode())
                self.logger.debug(f"Mensaje enviado a {neighbor_id}")
                return True
        except Exception as e:
            self.logger.error(f"Error enviando mensaje a {neighbor_id}: {e}")
            # Eliminar socket problemático
            if neighbor_id in self.client_sockets:
                del self.client_sockets[neighbor_id]
        return False

    #Reenvía mensaje a todos los vecinos conectados
    def flood_message(self, message, exclude_neighbor=None):
        sent_count = 0
        for neighbor_id in self.client_sockets:
            if neighbor_id != exclude_neighbor:
                if self.send_message(message, neighbor_id):
                    sent_count += 1
        return sent_count

    def start(self, node_addresses):
        # Iniciar servidor
        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Iniciar algoritmo de routing
        routing_thread = threading.Thread(target=self.routing_algorithm.start)
        routing_thread.daemon = True
        routing_thread.start()
        
        # Conectar a vecinos (en segundo plano con reintentos)
        self.connect_to_neighbors(node_addresses)
        
        self.logger.info(f"Nodo {self.node_id} iniciado")
        
        # Bucle principal simple
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Cerrando nodo")
            self.shutdown()

    def shutdown(self):
        self.running = False
        for sock in self.client_sockets.values():
            sock.close()
        self.server_socket.close()
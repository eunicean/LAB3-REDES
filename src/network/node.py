import socket
import threading
import json
import time
from src.algorithms.flooding import Flooding
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
        
        # Configurar logger (sin archivo por defecto para simplificar)
        self.logger = setup_logger(node_id)
        
        # Configurar el algoritmo de routing
        self.routing_algorithm.set_node(self)

    def start_server(self):
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.logger.info(f"Escuchando en {self.host}:{self.port}")
            
            while True:
                client_socket, addr = self.server_socket.accept()
                self.logger.debug(f"Conexión aceptada de {addr}")
                threading.Thread(target=self.handle_client, args=(client_socket,)).start()
        except Exception as e:
            self.logger.error(f"Error en servidor: {e}")

    def connect_to_neighbors(self, node_addresses):
        for neighbor_id, cost in self.neighbors.items():
            if neighbor_id in node_addresses:
                host, port_str = node_addresses[neighbor_id].split(':')
                port = int(port_str)
                
                max_retries = 2
                for attempt in range(max_retries):
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.connect((host, port))
                        self.client_sockets[neighbor_id] = sock
                        self.logger.info(f"Conectado a vecino {neighbor_id} en {host}:{port}")
                        break
                    except Exception as e:
                        self.logger.warning(f"Intento {attempt+1} de conexión a {neighbor_id} falló: {e}")
                        time.sleep(2)
                        if attempt == max_retries - 1:
                            self.logger.error(f"No se pudo conectar a {neighbor_id} después de {max_retries} intentos")

    def send_message(self, message, neighbor_id):
        try:
            if neighbor_id in self.client_sockets:
                sock = self.client_sockets[neighbor_id]
                sock.send(json.dumps(message).encode())
                self.logger.debug(f"Mensaje enviado a {neighbor_id}: {message}")
                return True
        except Exception as e:
            self.logger.error(f"Error enviando mensaje a {neighbor_id}: {e}")
            if neighbor_id in self.client_sockets:
                del self.client_sockets[neighbor_id]
        return False

    def flood_message(self, message, exclude_neighbor=None):
        sent_count = 0
        for neighbor_id in self.neighbors:
            if neighbor_id != exclude_neighbor:
                if self.send_message(message, neighbor_id):
                    sent_count += 1
        self.logger.info(f"Mensaje reenviado a {sent_count} vecinos")
        return sent_count

    def handle_client(self, client_socket):
        try:
            data = client_socket.recv(4096).decode()
            if not data:
                return
            
            message = json.loads(data)
            self.logger.info(f"Mensaje recibido: {message}")
            
            # Delegar el procesamiento al algoritmo de routing
            self.routing_algorithm.handle_message(message, client_socket.getpeername())
            
        except json.JSONDecodeError:
            self.logger.error("Mensaje JSON mal formado")
        except Exception as e:
            self.logger.error(f"Error manejando cliente: {e}")
        finally:
            client_socket.close()

    def start(self, node_addresses):
        # Conectar a vecinos
        self.connect_to_neighbors(node_addresses)
        
        # Iniciar servidor en un hilo
        server_thread = threading.Thread(target=self.start_server)
        server_thread.daemon = True
        server_thread.start()
        
        # Iniciar proceso de routing en un hilo
        routing_thread = threading.Thread(target=self.routing_algorithm.start)
        routing_thread.daemon = True
        routing_thread.start()
        
        self.logger.info(f"Nodo {self.node_id} iniciado con vecinos: {list(self.neighbors.keys())}")
        
        # Mantener el nodo activo
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Cerrando nodo")
            self.shutdown()

    def shutdown(self):
        for sock in self.client_sockets.values():
            sock.close()
        self.server_socket.close()
        self.routing_algorithm.shutdown()
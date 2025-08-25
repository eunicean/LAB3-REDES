import threading
import time
import json

class Flooding:
    def __init__(self):
        self.node = None
        self.seen_messages = set()
        self.running = False
        self.lock = threading.Lock()

    def set_node(self, node):
        self.node = node

    def handle_message(self, message, source_addr):
        with self.lock:
            # Crear un ID único para el mensaje
            message_id = f"{message.get('from', '')}_{message.get('timestamp', 0)}_{message.get('payload', '')}"
            
            # Si ya hemos visto este mensaje, ignorarlo
            if message_id in self.seen_messages:
                self.node.logger.debug(f"Mensaje duplicado ignorado: {message_id}")
                return
            
            self.seen_messages.add(message_id)
            
            # Decrementar TTL
            message['ttl'] = message.get('ttl', 5) - 1
            
            # Si el TTL llegó a cero, no reenviar
            if message['ttl'] <= 0:
                self.node.logger.debug("TTL agotado, descartando mensaje")
                return
            
            # Si el mensaje es para este nodo, procesarlo
            if message.get('to') == self.node.node_id:
                self.node.logger.info(f"Mensaje para este nodo: {message.get('payload')}")
                self.node.logger.info(f"Mensaje llego al destino")
                
            else:
                # Reenviar a todos los vecinos excepto al que nos lo envió
                source_neighbor = None
                for neighbor_id, socket in self.node.client_sockets.items():
                    if socket.getpeername() == source_addr:
                        source_neighbor = neighbor_id
                        break
                
                sent_count = self.node.flood_message(message, exclude_neighbor=source_neighbor)
                self.node.logger.info(f"Mensaje reenviado a {sent_count} vecinos")

    def start(self):
        self.running = True
        self.node.logger.info("Algoritmo de flooding iniciado")
        
        while self.running:
            # El flooding es reactivo, no necesita hacer nada periódicamente
            time.sleep(1)

    def shutdown(self):
        self.running = False
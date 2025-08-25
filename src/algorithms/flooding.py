import threading
import time

class Flooding:
    def __init__(self):
        self.node = None
        self.seen_messages = set()
        self.running = False

    def set_node(self, node):
        self.node = node

    def handle_message(self, message):
        # Usar campos estándar del protocolo
        message_id = f"{message.get('from', '')}_{message.get('payload', '')}"
        
        if message_id in self.seen_messages:
            self.node.logger.info(f"Mensaje ya recibido: {message.get('payload')}, no se propaga")
            return
            
        self.seen_messages.add(message_id)
        
        # Manejar TTL según protocolo
        ttl = message.get('ttl', 5) - 1
        if ttl <= 0:
            self.node.logger.debug("TTL agotado")
            return
            
        message['ttl'] = ttl
        
        # Verificar si es para este nodo
        if message.get('to') == self.node.node_id:
            self.node.logger.info(f"Mensaje ha llegado al destino: {message.get('payload')}")
        else:
            # Reenviar a todos los vecinos excepto al remitente
            self.node.flood_message(message, exclude_neighbor=message.get('from'))

    def start(self):
        self.running = True
        self.node.logger.info("Nodo inicializandose")
        
        while self.running:
            time.sleep(1)

    def shutdown(self):
        self.running = False
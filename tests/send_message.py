import sys
import os

# Agregar el directorio raíz del proyecto al path de Python
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Ahora importamos los módulos de src
from src.utils.config_loader import load_config, get_node_addresses

import socket
import json
import time

def send_message(target_node, message_data):
    """Envía un mensaje a un nodo específico"""
    try:
        # Cargar configuración
        names_config = load_config('config/names-ejemplo.json')
        node_addresses = get_node_addresses(names_config)
        
        if target_node not in node_addresses:
            print(f"Error: Nodo {target_node} no encontrado")
            return False
        
        target_address = node_addresses[target_node]
        host, port_str = target_address.split(':')
        port = int(port_str)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.send(json.dumps(message_data).encode())
        sock.close()
        
        print(f"Mensaje enviado a {target_node} ({host}:{port})")
        return True
        
    except Exception as e:
        print(f"Error enviando mensaje: {e}")
        return False

def main():
    if len(sys.argv) < 4:
        print("Uso: python tests/send_message.py <nodo_origen> <nodo_destino> <mensaje>")
        print("Ejemplo: python tests/send_message.py A G 'Hola mundo'")
        sys.exit(1)
    
    from_node = sys.argv[1]
    to_node = sys.argv[2]
    message_text = ' '.join(sys.argv[3:])
    
    message = {
        "proto": "flooding",
        "type": "message",
        "from": from_node,
        "to": to_node,
        "ttl": 10,
        "headers": [],
        "payload": message_text,
        "timestamp": int(time.time())
    }
    
    send_message(from_node, message)

if __name__ == '__main__':
    main()
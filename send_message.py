import socket
import json
import sys

def send_message(target_host, target_port, message):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((target_host, target_port))
        sock.send(json.dumps(message).encode())
        sock.close()
        print(f"Mensaje enviado a {target_host}:{target_port}")
    except Exception as e:
        print(f"Error enviando mensaje: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python send_message.py <host> <port> <mensaje>")
        sys.exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    message_text = sys.argv[3] if len(sys.argv) > 3 else "Hola, mundo!"
    
    message = {
        "proto": "flooding",
        "type": "message",
        "from": "EXTERNAL",
        "to": "G",  # Destino final
        "ttl": 10,
        "headers": [],
        "payload": message_text,
        "timestamp": 1234567890  # Usar timestamp real en producción
    }
    
    send_message(host, port, message)
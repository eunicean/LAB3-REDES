import sys
import os
import subprocess
import time
import signal
import threading
import json
import socket
import argparse

# Agregar el directorio raíz del proyecto al path de Python
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.utils.config_loader import load_config, get_node_addresses

class NetworkManager:
    def __init__(self):
        self.processes = {}
        self.running = False
        self.logs = {}  # Almacenar logs por nodo
        
        # Cargar configuración
        self.names_config = load_config('config/names-ejemplo.json')
        self.node_addresses = get_node_addresses(self.names_config)
    
    def start_all_nodes(self, algorithm='flooding'):
        """Inicia todos los nodos de la red"""
        self.running = True
        print(f"Iniciando todos los nodos de la red con algoritmo: {algorithm}")
        print("Los logs de cada nodo se mostrarán a continuación:")
        print("=" * 60)
        
        for node_id in self.node_addresses.keys():
            self.start_node(node_id, algorithm)
            time.sleep(1)  # Pausa más larga para evitar congestión
        
        print("=" * 60)
        print("Todos los nodos iniciados. Presiona Ctrl+C para detener.")
    
    def start_node(self, node_id, algorithm='flooding'):
        """Inicia un nodo específico"""
        try:
            # Crear archivo de log individual para cada nodo
            log_dir = os.path.join(project_root, 'logs')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            log_file = os.path.join(log_dir, f'{node_id}.log')
            
            # Iniciar proceso con output redirigido a archivo y consola
            process = subprocess.Popen([
                sys.executable, "main.py", node_id, "--algorithm", algorithm
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
               text=True, bufsize=1, universal_newlines=True)
            
            self.processes[node_id] = process
            self.logs[node_id] = []
            
            print(f"Nodo {node_id} iniciado (PID: {process.pid})")
            
            # Hilos para capturar output en tiempo real
            threading.Thread(target=self.capture_stdout, args=(node_id, process), daemon=True).start()
            threading.Thread(target=self.capture_stderr, args=(node_id, process), daemon=True).start()
            
        except Exception as e:
            print(f"Error iniciando nodo {node_id}: {e}")
    
    def capture_stdout(self, node_id, process):
        """Captura stdout en tiempo real"""
        try:
            while self.running and process.poll() is None:
                line = process.stdout.readline()
                if line:
                    clean_line = line.strip()
                    if clean_line:
                        print(f"[{node_id}] {clean_line}")
                        self.logs[node_id].append(clean_line)
                time.sleep(0.1)
        except Exception as e:
            print(f"Error capturando stdout de {node_id}: {e}")
    
    def capture_stderr(self, node_id, process):
        """Captura stderr en tiempo real"""
        try:
            while self.running and process.poll() is None:
                line = process.stderr.readline()
                if line:
                    clean_line = line.strip()
                    if clean_line:
                        # Detectar si es realmente un ERROR o solo un log normal
                        if any(keyword in clean_line for keyword in ['ERROR', 'CRITICAL', 'FATAL']):
                            print(f"[{node_id}-ERROR] {clean_line}")
                        else:
                            print(f"[{node_id}-LOG] {clean_line}")
                        self.logs[node_id].append(clean_line)
                time.sleep(0.1)
        except Exception as e:
            print(f"Error capturando stderr de {node_id}: {e}")
    
    def stop_all_nodes(self):
        """Detiene todos los nodos"""
        self.running = False
        print("\nDeteniendo todos los nodos...")
        
        for node_id, process in self.processes.items():
            try:
                process.terminate()
                stdout, stderr = process.communicate(timeout=3)
                print(f"Nodo {node_id} detenido")
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                    print(f"Nodo {node_id} forzado a detenerse")
                except:
                    pass
            except Exception as e:
                print(f"Error deteniendo nodo {node_id}: {e}")
    
    def send_test_message(self, from_node, to_node, message_text, proto="flooding"):
        """Envía un mensaje de prueba y verifica delivery"""
        if from_node not in self.node_addresses:
            print(f"Error: Nodo {from_node} no existe")
            return
        
        target_address = self.node_addresses[from_node]
        host, port_str = target_address.split(':')
        port = int(port_str)
        
        message = {
            "proto": proto,
            "type": "message",
            "from": from_node,
            "to": to_node,
            "ttl": 10,
            "headers": [],
            "payload": message_text,
            "timestamp": int(time.time())
        }
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            sock.send(json.dumps(message).encode())
            sock.close()
            
            print(f"Mensaje enviado desde {from_node} a {to_node}: '{message_text}'")
            print("Revisa los logs para ver el trayecto del mensaje...")
            
        except Exception as e:
            print(f"Error enviando mensaje: {e}")
    
    def show_node_status(self):
        """Muestra el estado de todos los nodos"""
        print("\nESTADO DE LOS NODOS:")
        print("-" * 40)
        
        for node_id, process in self.processes.items():
            status = "ACTIVO" if process.poll() is None else "INACTIVO"
            print(f"{node_id}: {status}")
        
        print("-" * 40)
    
    def show_recent_logs(self, node_id, lines=5):
        """Muestra los logs recientes de un nodo"""
        if node_id in self.logs and self.logs[node_id]:
            print(f"\nÚltimos {lines} logs de {node_id}:")
            print("-" * 50)
            for log in self.logs[node_id][-lines:]:
                print(log)
            print("-" * 50)
        else:
            print(f"No hay logs disponibles para {node_id}")

def main():
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Gestor de red para Laboratorio 3')
    parser.add_argument('--algorithm', '-a', default='flooding', 
                       choices=['flooding', 'dijkstra', 'lsr', 'dvr'],
                       help='Algoritmo de enrutamiento a usar')
    parser.add_argument('--send', action='store_true',
                       help='Modo de envío rápido de mensajes')
    parser.add_argument('--from-node', help='Nodo origen para envío rápido')
    parser.add_argument('--to-node', help='Nodo destino para envío rápido')
    parser.add_argument('--message', help='Mensaje para envío rápido')
    
    args = parser.parse_args()
    
    # Agregar el path para los imports
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    # Modo de envío rápido
    if args.send:
        if not all([args.from_node, args.to_node, args.message]):
            print("Error: Modo send requiere --from-node, --to-node y --message")
            sys.exit(1)
        
        manager = NetworkManager()
        manager.send_test_message(args.from_node, args.to_node, args.message, args.algorithm)
        return
    
    # Modo completo: iniciar todos los nodos
    manager = NetworkManager()
    
    def signal_handler(sig, frame):
        print("\n\nSeñal de interrupción recibida...")
        manager.stop_all_nodes()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Iniciar todos los nodos con el algoritmo especificado
    manager.start_all_nodes(args.algorithm)
    
    # Pequeña pausa para que los nodos se inicialicen
    time.sleep(5)
    
    # Menú interactivo
    try:
        while True:
            print("\n" + "="*60)
            print("            MENÚ DE PRUEBAS - LAB3 REDES")
            print("="*60)
            print(f"Algoritmo actual: {args.algorithm}")
            print("1. Enviar mensaje de prueba")
            print("2. Mostrar estado de todos los nodos")
            print("3. Ver logs de un nodo específico")
            print("4. Ejecutar prueba automática")
            print("5. Cambiar algoritmo (requiere reinicio)")
            print("6. Salir y detener todos los nodos")
            print("="*60)
            
            choice = input("Selecciona una opción (1-6): ").strip()
            
            if choice == '1':
                print("\n--- ENVIAR MENSAJE ---")
                from_node = input("Nodo origen (ej: A): ").strip().upper()
                to_node = input("Nodo destino (ej: G): ").strip().upper()
                message = input("Mensaje: ").strip()
                
                if from_node and to_node and message:
                    manager.send_test_message(from_node, to_node, message, args.algorithm)
                    print("Revisa los logs arriba para ver el trayecto del mensaje")
                else:
                    print("Error: Debes completar todos los campos")
                    
            elif choice == '2':
                manager.show_node_status()
                
            elif choice == '3':
                node_id = input("¿Qué nodo quieres revisar? (ej: A): ").strip().upper()
                if node_id in manager.processes:
                    manager.show_recent_logs(node_id, lines=10)
                else:
                    print(f"Nodo {node_id} no encontrado")
                    
            elif choice == '4':
                print("\n--- PRUEBA AUTOMÁTICA ---")
                print("Enviando mensaje de prueba de A a G...")
                manager.send_test_message('A', 'G', 'Mensaje de prueba automática', args.algorithm)
                time.sleep(2)
                print("Prueba completada. Revisa los logs.")
                
            elif choice == '5':
                print("\n--- CAMBIAR ALGORITMO ---")
                print("Algoritmos disponibles: flooding, dijkstra, lsr, dvr")
                new_algorithm = input("Nuevo algoritmo: ").strip().lower()
                if new_algorithm in ['flooding', 'dijkstra', 'lsr', 'dvr']:
                    print(f"Reiniciando con algoritmo: {new_algorithm}")
                    manager.stop_all_nodes()
                    args.algorithm = new_algorithm
                    manager = NetworkManager()
                    manager.start_all_nodes(args.algorithm)
                    time.sleep(5)
                else:
                    print("Algoritmo no válido")
                    
            elif choice == '6':
                print("Saliendo...")
                break
                
            else:
                print("Opción no válida. Por favor elige 1-6.")
                
    except KeyboardInterrupt:
        print("\nInterrupción recibida...")
    
    finally:
        manager.stop_all_nodes()

if __name__ == '__main__':
    main()
import sys
import argparse
from src.utils.config_loader import load_config, get_node_addresses, get_neighbors
from src.network.node import Node
from src.algorithms.flooding import Flooding
from src.algorithms.dijkstra import Dijkstra

def main():
    parser = argparse.ArgumentParser(description='Nodo de red con algoritmo de enrutamiento')
    parser.add_argument('node_id', help='ID del nodo (ej: A, B, C)')
    parser.add_argument('--algorithm', '-a', default='flooding', 
                        choices=['flooding', 'dijkstra', 'lsr', 'dvr'],
                        help='Algoritmo de enrutamiento a usar')
    args = parser.parse_args()
    
    node_id = args.node_id
    algorithm_name = args.algorithm
    
    # Cargar configuraciones
    try:
        topo_config = load_config('config/topo-ejemplo.json')
        names_config = load_config('config/names-ejemplo.json')
    except Exception as e:
        print(f"Error cargando configuración: {e}")
        return
    
    # Obtener información del nodo
    neighbors = get_neighbors(topo_config, node_id)
    node_addresses = get_node_addresses(names_config)
    
    if node_id not in node_addresses:
        print(f"Error: Nodo {node_id} no encontrado en la configuración")
        return
        
    node_address = node_addresses[node_id]
    host, port_str = node_address.split(':')
    port = int(port_str)
    
    # Aqui es donde se verifica el tipo de algoritmo, hay que poner otro if para cada
    # algoritmo que vayamos a implementar
    ########################################################################################################
    # AQUI es donde se agregan algoritmos posibles
    if algorithm_name == 'flooding':
        routing_algorithm = Flooding()
    elif algorithm_name == 'dijkstra':
        routing_algorithm = Dijkstra()
        # Para Dijkstra, cargamos la topología completa
        routing_algorithm.build_topology_from_config(topo_config)
    else:
        # Para otros algoritmos 
        print(f"Algoritmo {algorithm_name} no implementado aún, usando flooding")
        routing_algorithm = Flooding()
    
    # Crear e iniciar el nodo
    node = Node(node_id, neighbors, host, port, routing_algorithm)
    
    if algorithm_name == 'dijkstra':
        routing_algorithm.calculate_routes()

    try:
        node.start(node_addresses)
    except KeyboardInterrupt:
        print("Interrupción recibida, cerrando nodo")
    except Exception as e:
        print(f"Error iniciando nodo: {e}")
    finally:
        node.shutdown()

if __name__ == '__main__':
    main()
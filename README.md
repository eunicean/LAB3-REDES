# LAB3-REDES
Algoritmos de Enrutamiento

### Resumen

En pocas palabras, lo que estamos haciendo es simular algoritmos de enrutamiento para poder transmitir mensajes entre nodos. Cada nodo es una representación de un dispositivo de red. Es decir, un nodo puede conectarse a otros nodos mediante Soquets (para la fase 1). Un nodo es un dispositivo dentro de una red.

## Archivos importantes

### config/topo-ejemplo.json
```json
{
  "type": "topo",
  "config": {
    "A": {"B": 7, "C": 7, "I": 1},
    "B": {"A": 7, "F": 2},
    "C": {"A": 7, "D": 5},
    "D": {"E": 1, "C": 5, "I": 6, "F": 1},
    "E": {"D": 1, "G": 1},
    "F": {"B": 2, "D": 1, "G": 3, "H": 4},
    "G": {"F": 3, "E": 4},
    "H": {"F": 4},
    "I": {"A": 1, "D": 6}
  }
}
```

El archivo que contiene la topología completa que se menciona en las instrucciones del laboratorio. Se incluye la información de nodo de origen, destino y el costo/distancia de un nodo a otro. Los datos que se usan y son necesarios de este json dependen del algoritmo.

### config/names-ejemplo.json
```json
{
  "type": "names",
  "config": {
    "A": "localhost:10000",
    "B": "localhost:10001",
    "C": "localhost:10002",
    "D": "localhost:10003",
    "E": "localhost:10004",
    "F": "localhost:10005",
    "G": "localhost:10006",
    "H": "localhost:10007",
    "I": "localhost:10008"
  }
}
```

### Protocolo de comunicación
Todos los mensajes siguen un formato específico
```json
{
  "type": "message|echo|info|hello|...",
  "from": "node_id",
  "to": "node_id",
  "ttl": 5,
  "headers": [{"opcional": "foo"}, ...],
  "payload": "contenido del mensaje"
}
```
Este es el protocolo de comunicación

### Funcionamiento de los algoritmos

Estos se encuentran dentro de la carpeta de algorithms. La idea es que estos algoritmos utilisen los nodos para poderhacer los algoritmos de enrutamiento. Los nodos tienen un atributo llamado routing_algorithm, el cual es una clase. Cada algoritmo es una clase que se guarda en dicha variable, para que ese nodo use algoritmo. La estructura de un algoritmo es así para flooding por ejemplo:


```python
class Flooding:
    def __init__(self):
        self.node = None
        self.seen_messages = set()
        self.running = False

    def set_node(self, node):
        self.node = node

    def handle_message(self, message):
        # Lógica específica del algoritmo
        pass

    def start(self):
        # Inicialización del algoritmo
        self.running = True

    def shutdown(self):
        # Limpieza
        self.running = False

```

La implementación de un algoritmo puede involucrar también cambios en el node.py, pero depende del caso también.

### logger.py

Es un archivo que tiene como objetivo hacer loggs de los eventos que ocurren en los nodos. Sirve para debuggeo y demostrar el funcionamiento.

### main.py

Este archivo es el que se encarga de levantar un nodo en específico, no la red completa. Por ejemplo con los comandos

```
python main.py A --algorithm flooding
python main.py B --algorithm flooding
```

Se levantan 2 nodos usando el algoritmo de flooding en ambos, estos nodos se levantan con la ayuda del archivo de configuración config_loader. Este prácticamente carga los json necesarios con la información de la topología. Pero levantar 8 terminales para poder probar el funcionamiento es tedioso, es por eso que también se hizo un script para poder levantar la red completa. OSea crear todos los nodos y sus conexiones siempre usando la topología.

IMPORTANTE: El algoritmo debe estar dentro de las opciones de main.py, al inicializar el nodo se ve si el algoritmo existe o no

### tests/run_network

Es un script que levanta todos los nodos luego de unos segundos y da la opción de enviar mensajes, ver los loggs luego de enviar un mensaje, enviar un mensaje especificando datos, un mensaje predeterminado. El algoritmo con el que se levanta la red se cambia dentro del codigo de run_network.py. Uso:

```
python tests/run_network.py
```

### tests/send_message.py
Es otro script de prueba para mandar un mensaje una vez está levantada la red, ya sea manualmente nodo por nodo o bien con el run_network

```
python tests/send_message.py A G "Mensaje de prueba"
```


# Pendientes

1. Implementar 2 algoritmos más de routing
2. Mejorar run_network para que reciba el algoritmo con el que se levanta la red en la terminal en lugar de que sea en el código
3. Makefile
4. Fase 2 xmpp
5. forwardin y routing ahora mismo estan vacios
6. La carpeta transport también tiene archivos vacios


# NOTA

Para implementar un algoritmo nuevo es im portan ver los archivos:
1. node.py
2. El archivo de su respectivo algoritmo
3. main.py




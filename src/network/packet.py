import json

def create_packet(proto, type, from_node, to_node, ttl, headers, payload):
    return {
        "proto": proto,
        "type": type,
        "from": from_node,
        "to": to_node,
        "ttl": ttl,
        "headers": headers,
        "payload": payload
    }

def decode_packet(data):
    return json.loads(data)
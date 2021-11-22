
import zmq

import json
from argparse import ArgumentParser

def put(sock_proxy: zmq.Socket, message: str):
    sock_proxy.send_string(message)
    _ = sock_proxy.recv_string()
    print(f'PUT message: {message}')

def main():
    parser = ArgumentParser(description='Process that publishes messages to topics.')
    
    parser.add_argument('port', help='publisher listening port')
    parser.add_argument('proxy_port', type=int, help='port of the proxy to connect to')
    parser.add_argument('--proxy_addr', help='address of the proxy to connect to (defaults to localhost)',
        default='127.0.0.1', metavar='ADDR')

    args = parser.parse_args()

    context = zmq.Context()

    # Connect to proxy
    sock_proxy = context.socket(zmq.REQ)
    sock_proxy.connect(f'tcp://{args.proxy_addr}:{args.proxy_port}')

    # Socket for listening to commands
    sock_rpc = context.socket(zmq.ROUTER)
    sock_rpc.bind(f'tcp://*:{args.port}')

    print(f'Publisher online...')

    while True:
        parts = sock_rpc.recv_multipart()
        command = json.loads(parts[2].decode('utf-8'))
        
        if (isinstance(command, dict) 
            and set(['method', 'message']).issubset(command.keys())
            and command['method'] == 'PUT'):
            put(sock_proxy, command['message'])

            parts[2] = b'OK'
        else:
            parts[2] = b'Error: malformed command'
        
        sock_rpc.send_multipart(parts)


if __name__ == '__main__':
    main()


import zmq
from argparse import ArgumentParser

def put(sock_proxy: zmq.Socket, message: str):
    print('PUT message: ', message)
    sock_proxy.send_string(message)

def main():
    parser = ArgumentParser(description='Process that publishes messages to topics.')
    
    parser.add_argument('id', help='id of the publisher')
    parser.add_argument('port', help='publisher listening port')
    parser.add_argument('proxy_addr', help='address of the proxy to connect to')
    parser.add_argument('proxy_port', type=int, help='port of the proxy to connect to')

    args = parser.parse_args()

    context = zmq.Context()

    # Connect to proxy
    sock_proxy = context.socket(zmq.PUB)
    sock_proxy.connect(f'tcp://{args.proxy_addr}:{args.proxy_port}')

    # Socket for listening to commands
    sock_rpc = context.socket(zmq.REP)
    sock_rpc.bind(f'tcp://*:{args.port}')

    print(f'Publisher #{args.id} online...')

    while True:
        command = sock_rpc.recv_json()
        
        if (isinstance(command, dict) 
            and set(['method', 'message']).issubset(command.keys())
            and command['method'] == 'PUT'):
            put(sock_proxy, command['message'])
            sock_rpc.send_string('OK')
        else:
            sock_rpc.send_string('Error')


if __name__ == '__main__':
    main()

import zmq
from argparse import ArgumentParser

def process_command(sock_proxy: zmq.Socket, command: dict):
    commands = {
        'GET': get,
        'SUB': sub,
        'UNSUB': unsub,
    }

    if (isinstance(command, dict)
        and set(['method', 'topic']).issubset(command.keys())
        and command['method'] in commands.keys()):
        commands['method'](sock_proxy, command['topic'])
        return True

    return False

def get(sock_proxy: zmq.Socket, topic: str):
    string = sock_proxy.recv_string() # TODO: get string from specific topic
    print(string)

def sub(sock_proxy: zmq.Socket, topic: str):
    sock_proxy.setsockopt_string(zmq.SUBSCRIBE, topic)

def unsub(sock_proxy: zmq.Socket, topic: str):
    sock_proxy.setsockopt_string(zmq.UNSUBSCRIBE, topic)

def main():
    parser = ArgumentParser(description='Process that subscribes to topics and receives messages.')
    
    parser.add_argument('id', help='id of the subscriber')
    parser.add_argument('port', help='subscriber listening port')
    parser.add_argument('proxy_addr', help='address of the proxy to connect to')
    parser.add_argument('proxy_port', type=int, help='port of the proxy to connect to')

    args = parser.parse_args()

    context = zmq.Context()

    # Connect to proxy
    sock_proxy = context.socket(zmq.SUB)
    sock_proxy.connect(f'tcp://{args.proxy_addr}:{args.proxy_port}')
    
    # Socket for listening to commands
    sock_rpc = context.socket(zmq.REP)
    sock_rpc.bind(f'tcp://*:{args.port}')

    print(f'Subscriber #{args.id} online...')

    sock_proxy.setsockopt(zmq.SUBSCRIBE, b'test')

    while True:
        command = sock_rpc.recv_json()

        ok = process_command(sock_proxy, command)

        if ok:
            sock_rpc.send_string('OK')
        else:
            sock_rpc.send_string('Error') 

if __name__ == '__main__':
    main()


import zmq
from argparse import ArgumentParser

def main():
    parser = ArgumentParser(description='Process that subscribes to topics and receives messages.')
    
    parser.add_argument('id', help='id of the subscriber')
    parser.add_argument('proxy_addr', help='address of the proxy to connect to')
    parser.add_argument('proxy_port', type=int, help='port of the proxy to connect to')

    args = parser.parse_args()

    context = zmq.Context()

    # Connect to proxy
    socket = context.socket(zmq.SUB)
    socket.connect(f'tcp://{args.proxy_addr}:{args.proxy_port}')

    print(f'Subscriber #{args.id} online...')

    socket.setsockopt(zmq.SUBSCRIBE, b'test')

    while True:
        string = socket.recv_string()
        print(string)

if __name__ == '__main__':
    main()

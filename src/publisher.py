
from time import sleep
import zmq
from argparse import ArgumentParser

def main():
    parser = ArgumentParser(description='Process that publishes messages to topics.')
    
    parser.add_argument('id', help='id of the publisher')
    parser.add_argument('proxy_addr', help='address of the proxy to connect to')
    parser.add_argument('proxy_port', type=int, help='port of the proxy to connect to')

    args = parser.parse_args()

    context = zmq.Context()

    # Connect to proxy
    socket = context.socket(zmq.PUB)
    socket.connect(f'tcp://{args.proxy_addr}:{args.proxy_port}')

    print(f'Publisher #{args.id} online...')

    num = 1
    while True:
        socket.send_string(f'test #{num}')
        num += 1
        sleep(3)

if __name__ == '__main__':
    main()
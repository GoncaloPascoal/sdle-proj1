
from argparse import ArgumentParser

def main():
    parser = ArgumentParser(description='Process that publishes messages to topics.')
    
    parser.add_argument('id', help='id of the publisher')
    parser.add_argument('proxy_addr', help='address of the proxy to connect to')
    parser.add_argument('proxy_port', type=int, help='port of the proxy to connect to')

    args = parser.parse_args()
    
    print(f'Publisher #{args.id} online...')

if __name__ == '__main__':
    main()

import zmq
from argparse import ArgumentParser

def main():
    parser = ArgumentParser(description='Proxy that acts as an intermediary \
            between publishers and subscribers, so that subscribers and \
            publishers do not need to know about each other.')

    parser.add_argument('publisher_port', type=int, help='port where publishers \
            can connect to')
    parser.add_argument('subscriber_port', type=int, help='port where subscribers \
            can connect to')

    args = parser.parse_args()

    context = zmq.Context()

    # Socket for publishers
    frontend = context.socket(zmq.XSUB)
    frontend.connect(f'tcp://127.0.0.1:{args.publisher_port}')
    
    # Socket for subscribers
    backend = context.socket(zmq.XPUB)
    backend.bind(f'tcp://127.0.0.1:{args.subscriber_port}')

    # Run the proxy
    zmq.proxy(frontend, backend)

    frontend.close()
    backend.close()
    context.destroy()

if __name__ == '__main__':
    main()
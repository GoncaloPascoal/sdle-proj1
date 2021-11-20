
import zmq

import pickle, os
from threading import Thread
from argparse import ArgumentParser
from time import sleep

from utils import Pipe

BACKUP_INTERVAL_MS = 250
TOPIC_TO_MSGS = {}

def parse_msg(parts):
    r_id = int.from_bytes(parts[0], byteorder='big')
    msg = parts[1].decode('utf-8')

    return r_id, msg

def listen(pipe_end: zmq.Socket):
    while True:
        try:
            msg = pipe_end.recv()
            print(f'Message: {msg}')
        except zmq.ZMQError as e:
            if e.errno == zmq.ETERM:
                break

def save_state():
    while True:
        f = open('service.obj', 'wb')
        pickle.dump(TOPIC_TO_MSGS, f)
        sleep(BACKUP_INTERVAL_MS / 1000)

def main():
    parser = ArgumentParser(description='Proxy that acts as an intermediary \
            between publishers and subscribers, so that subscribers and \
            publishers do not need to know about each other.')

    parser.add_argument('publisher_port', type=int, help='port where publishers \
            can connect to')
    parser.add_argument('subscriber_port', type=int, help='port where subscribers \
            can connect to')

    args = parser.parse_args()

    if os.path.exists('service.obj'):
        f = open('service.obj', 'rb')
        TOPIC_TO_MSGS = pickle.load(f)

    context = zmq.Context()

    # Socket for publishers
    sock_pub = context.socket(zmq.ROUTER)
    sock_pub.bind(f'tcp://*:{args.publisher_port}')
    
    # Socket for subscribers
    sock_sub = context.socket(zmq.XPUB)
    sock_sub.bind(f'tcp://*:{args.subscriber_port}')

    pipe = Pipe(context)
    listener = Thread(target=listen, args=(pipe.sock_in,))
    listener.start()

    zmq.proxy(sock_sub, pipe.sock_out)

    thread_state = Thread(target=save_state)
    thread_state.start()

    while True:
        parts = sock_pub.recv_multipart()
        _, msg = parse_msg(parts)
        sock_sub.send_string(msg)

        print(msg)

        for t, q in TOPIC_TO_MSGS.items():
            if msg.startswith(t):
                q.put(msg)

        parts[1] = b''
        sock_pub.send_multipart(parts)

if __name__ == '__main__':
    main()